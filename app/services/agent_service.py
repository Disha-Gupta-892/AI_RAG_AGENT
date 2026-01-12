"""
AI Agent Service.
Core agent logic that decides between direct LLM response and RAG-based retrieval.
Implements tool calling and query classification.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from app.core.config import settings
from app.models.schemas import QueryType, AskResponse, DocumentSource
from app.services.azure_openai_service import get_azure_openai_service
from app.services.rag_service import get_rag_service
from app.services.session_service import get_session_service
from datetime import datetime

logger = logging.getLogger(__name__)


# Tool definitions for the agent
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search through company documents to find relevant information. Use this when the user asks about company policies, product information, technical documentation, FAQs, or any topic that might be covered in internal documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant documents"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


CLASSIFICATION_SYSTEM_PROMPT = """You are an intelligent AI assistant that helps users by either answering questions directly or searching through company documents.

You have access to a tool called 'search_documents' that can search through company documents including:
- Company policies and guidelines
- Product information and FAQs
- Technical documentation
- HR policies and procedures

DECISION CRITERIA:
1. Use 'search_documents' tool when the user asks about:
   - Company-specific policies (remote work, leave, benefits, etc.)
   - Product details, features, or specifications
   - Technical procedures or documentation
   - FAQs or common questions about the company/products
   - Any topic that would be in internal company documents

2. Answer DIRECTLY without using tools when:
   - The user asks general knowledge questions not related to company documents
   - The user asks for explanations of general concepts
   - The user makes casual conversation or greetings
   - The question is about common knowledge that doesn't require document lookup

Always be helpful and provide clear, accurate responses."""


RAG_RESPONSE_PROMPT = """You are a helpful AI assistant. Use the following retrieved context to answer the user's question.

RETRIEVED CONTEXT:
{context}

INSTRUCTIONS:
1. Answer based primarily on the provided context
2. If the context doesn't fully answer the question, acknowledge what you found and what's missing
3. Be concise but comprehensive
4. Cite the source documents when providing information
5. If the context is empty or irrelevant, say you couldn't find relevant information in the documents

USER QUESTION: {question}"""


class AgentService:
    """
    AI Agent service that orchestrates query processing.
    Implements the decision logic between direct LLM response and RAG retrieval.
    """
    
    def __init__(self):
        """Initialize the agent service."""
        self.openai_service = get_azure_openai_service()
        self.rag_service = get_rag_service()
        self.session_service = get_session_service()
        logger.info("Agent Service initialized")

    def _classify_and_process_query(
        self, 
        query: str, 
        conversation_history: List[dict]
    ) -> Tuple[QueryType, Optional[str]]:
        """
        Classify query and determine processing method using tool calling.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            
        Returns:
            Tuple of (query_type, search_query if RAG needed)
        """
        messages = [
            {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT}
        ]
        
        # Add conversation history for context
        messages.extend(conversation_history[-6:])  # Last 3 exchanges
        messages.append({"role": "user", "content": query})
        
        try:
            # Call LLM with tools to let it decide
            response = self.openai_service.client.chat.completions.create(
                model=self.openai_service.chat_deployment,
                messages=messages,
                tools=AGENT_TOOLS,
                tool_choice="auto",
                temperature=0.3
            )
            
            message = response.choices[0].message
            
            # Check if the model wants to use a tool
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "search_documents":
                        args = json.loads(tool_call.function.arguments)
                        search_query = args.get("query", query)
                        logger.info(f"Agent decided to use RAG with query: {search_query}")
                        return QueryType.RAG, search_query
            
            # No tool call - direct response
            logger.info("Agent decided to answer directly")
            return QueryType.DIRECT, None
            
        except Exception as e:
            logger.error(f"Error in query classification: {e}")
            # Default to RAG on error to be safe
            return QueryType.RAG, query

    def _generate_direct_response(
        self, 
        query: str, 
        conversation_history: List[dict]
    ) -> str:
        """
        Generate a direct LLM response without document retrieval.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            
        Returns:
            Generated response
        """
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."}
        ]
        messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": query})
        
        return self.openai_service.get_chat_completion(messages)

    def _generate_rag_response(
        self, 
        query: str, 
        search_query: str,
        conversation_history: List[dict]
    ) -> Tuple[str, List[str]]:
        """
        Generate a response using RAG pipeline.
        
        Args:
            query: Original user query
            search_query: Query for document search
            conversation_history: Previous conversation messages
            
        Returns:
            Tuple of (response, source_list)
        """
        # Retrieve relevant context
        context, sources = self.rag_service.get_context_for_query(search_query)
        
        if not context:
            # No relevant documents found
            return (
                "I couldn't find relevant information in the documents to answer your question. "
                "Could you please rephrase or ask about a different topic?",
                []
            )
        
        # Generate response with context
        prompt = RAG_RESPONSE_PROMPT.format(context=context, question=query)
        
        messages = [{"role": "system", "content": prompt}]
        # Add some history for continuity
        messages.extend(conversation_history[-4:])
        messages.append({"role": "user", "content": query})
        
        response = self.openai_service.get_chat_completion(messages, temperature=0.5)
        return response, sources

    async def process_query(
        self, 
        query: str, 
        session_id: Optional[str] = None
    ) -> AskResponse:
        """
        Process a user query through the agent pipeline.
        
        Args:
            query: User's question
            session_id: Optional session identifier
            
        Returns:
            AskResponse with answer, sources, and metadata
        """
        # Get or create session
        session_id = self.session_service.get_or_create_session(session_id)
        
        # Get conversation history
        conversation_history = self.session_service.get_conversation_history(session_id)
        
        # Classify query and determine processing method
        query_type, search_query = self._classify_and_process_query(
            query, 
            conversation_history
        )
        
        # Process based on classification
        if query_type == QueryType.DIRECT:
            answer = self._generate_direct_response(query, conversation_history)
            sources = []
        else:
            answer, sources = self._generate_rag_response(
                query, 
                search_query or query,
                conversation_history
            )
        
        # Update session history
        self.session_service.add_message(session_id, "user", query)
        self.session_service.add_message(session_id, "assistant", answer)
        
        return AskResponse(
            answer=answer,
            sources=sources,
            query_type=query_type,
            session_id=session_id,
            timestamp=datetime.utcnow()
        )


# Singleton instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """
    Get or create the agent service singleton.
    
    Returns:
        AgentService instance
    """
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
