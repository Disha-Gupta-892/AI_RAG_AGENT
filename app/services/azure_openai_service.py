"""
Azure OpenAI Service module.
Handles all interactions with Azure OpenAI for chat completions and embeddings.
In demo mode, returns mock responses without API calls.
"""

import logging
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """
    Service class for Azure OpenAI operations.
    Provides methods for chat completions and embeddings generation.
    """
    
    def __init__(self):
        """Initialize the Azure OpenAI client."""
        from openai import AzureOpenAI
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.chat_deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self.embedding_deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
        logger.info("Azure OpenAI Service initialized successfully")

    def get_chat_completion(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a chat completion using Azure OpenAI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating chat completion: {e}")
            raise

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = []
            # Process in batches to avoid API limits
            batch_size = 16
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self.client.embeddings.create(
                    model=self.embedding_deployment,
                    input=batch
                )
                embeddings.extend([data.embedding for data in response.data])
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def get_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.get_embeddings([text])
        return embeddings[0]


# Singleton instance
_azure_openai_service = None


def get_azure_openai_service():
    """
    Get or create the Azure OpenAI service singleton.
    Returns mock service in demo mode.
    
    Returns:
        AzureOpenAIService or MockAzureOpenAIService instance
    """
    global _azure_openai_service
    
    if _azure_openai_service is None:
        if settings.DEMO_MODE:
            # Use mock service in demo mode
            from app.services.mock_openai_service import get_mock_openai_service
            _azure_openai_service = get_mock_openai_service()
            logger.info("Using MOCK OpenAI Service (Demo Mode)")
        else:
            # Use real Azure OpenAI service
            _azure_openai_service = AzureOpenAIService()
    
    return _azure_openai_service
