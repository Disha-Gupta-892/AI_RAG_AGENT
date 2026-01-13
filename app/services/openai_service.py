"""
Open-Source LLM Service using LangChain and Hugging Face.
Provides chat completions and embeddings using open-source models.
Compatible with existing Azure OpenAI interface.
"""

import logging
import os
import json
from typing import List, Optional, Any
from pathlib import Path
import torch
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)


class MockResponse:
    """Mock response object for compatibility with OpenAI SDK structure."""
    def __init__(self, content: str, tool_calls: Optional[List[Any]] = None):
        self.choices = [MockChoice(content, tool_calls)]

class MockChoice:
    """Mock choice object for compatibility with OpenAI SDK structure."""
    def __init__(self, content: str, tool_calls: Optional[List[Any]] = None):
        self.message = MockMessage(content, tool_calls)

class MockMessage:
    """Mock message object for compatibility with OpenAI SDK structure."""
    def __init__(self, content: str, tool_calls: Optional[List[Any]] = None):
        self.content = content
        self.tool_calls = tool_calls

class MockToolCall:
    """Mock tool call object for compatibility with OpenAI SDK structure."""
    def __init__(self, name: str, arguments: str):
        self.id = "call_" + name
        self.type = "function"
        self.function = MockFunction(name, arguments)

class MockFunction:
    """Mock function object for compatibility with OpenAI SDK structure."""
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class OpenSourceLLMService:
    """
    Service class for open-source LLM operations using LangChain and Hugging Face.
    Provides methods for chat completions and embeddings generation.
    """

    def __init__(self):
        """Initialize the open-source LLM service."""
        from app.core.config import settings
        self.device = 0 if torch.cuda.is_available() else -1
        self.model_name = settings.OPEN_SOURCE_CHAT_MODEL
        self.embedding_model_name = settings.OPEN_SOURCE_EMBEDDING_MODEL
        
        # Initialize chat model
        self._init_chat_model()

        # Initialize embeddings
        self._init_embeddings()

        # For compatibility with AgentService
        self.client = self
        logger.info("Open-Source LLM Service initialized successfully")

    def _init_chat_model(self):
        """Initialize the chat completion model."""
        try:
            logger.info(f"Loading chat model {self.model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device >= 0 else torch.float32,
                device_map="auto" if self.device >= 0 else None,
                low_cpu_mem_usage=True
            )

            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id if tokenizer.eos_token_id else 50256
            )

            self.llm = HuggingFacePipeline(pipeline=pipe)
            logger.info(f"Chat model {self.model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading chat model: {e}")
            # Fallback to a very small model if requested model fails
            if self.model_name != "gpt2":
                logger.warning("Attempting fallback to GPT-2...")
                self.model_name = "gpt2"
                self._init_chat_model()
            else:
                raise

    def _init_embeddings(self):
        """Initialize the embedding model."""
        try:
            logger.info(f"Loading embedding model {self.embedding_model_name}...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name,
                model_kwargs={'device': 'cuda' if self.device >= 0 else 'cpu'}
            )
            logger.info(f"Embedding model {self.embedding_model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise

    @property
    def chat(self):
        """Mock chat attribute for compatibility with OpenAI SDK."""
        return self

    @property
    def completions(self):
        """Mock completions attribute for compatibility with OpenAI SDK."""
        return self

    def create(self, model: str, messages: List[dict], tools: Optional[List[dict]] = None, **kwargs) -> MockResponse:
        """
        Mock create method for compatibility with OpenAI SDK.
        Handles both direct chat and tool-calling classification.
        """
        prompt = self._messages_to_prompt(messages)
        
        # If tools are provided, we need to decide if we should call search_documents
        # Simple keyword-based heuristic for open-source models that don't support native tool calling
        if tools:
            user_msg = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), "")
            if self._should_use_rag(user_msg):
                tool_call = MockToolCall(
                    name="search_documents",
                    arguments=json.dumps({"query": user_msg})
                )
                return MockResponse(content="", tool_calls=[tool_call])

        # Otherwise just generate text
        response_text = self.get_chat_completion(messages)
        return MockResponse(content=response_text)

    def _should_use_rag(self, query: str) -> bool:
        """Simple heuristic to decide if RAG is needed."""
        rag_keywords = [
            "policy", "info", "product", "guide", "how to", "docs", "company",
            "hr", "benefits", "leave", "remote", "pto", "401k", "password", "reset"
        ]
        query_lower = query.lower()
        return any(k in query_lower for k in rag_keywords)

    def get_chat_completion(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a chat completion."""
        try:
            prompt = self._messages_to_prompt(messages)
            # LangChain HuggingFacePipeline usage
            response = self.llm.invoke(prompt)
            
            # HuggingFacePipeline often returns the full prompt + completion
            # We want to extract just the completion
            if response.startswith(prompt):
                response = response[len(prompt):].strip()
            
            return response
        except Exception as e:
            logger.error(f"Error generating chat completion: {e}")
            return f"Error: {str(e)}"

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings."""
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def get_single_embedding(self, text: str) -> List[float]:
        """Generate single embedding."""
        return self.get_embeddings([text])[0]

    def _messages_to_prompt(self, messages: List[dict]) -> str:
        """Convert chat messages to a single prompt string."""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant: ")
        return "\n".join(prompt_parts)


# Singleton instance
_openai_service: Optional[OpenSourceLLMService] = None


def get_openai_service() -> OpenSourceLLMService:
    """Get or create the open-source LLM service singleton."""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenSourceLLMService()
    return _openai_service
