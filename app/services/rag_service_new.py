"""
RAG (Retrieval-Augmented Generation) Service.
Handles document processing, embedding storage, and retrieval using Azure AI Search.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from app.core.config import settings
from app.services.azure_openai_service import get_azure_openai_service

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of a document with metadata."""

    def __init__(self, content: str, document_name: str, chunk_index: int, id: str = None):
        self.content = content
        self.document_name = document_name
        self.chunk_index = chunk_index
        self.id = id or f"{document_name}_{chunk_index}"

    def __repr__(self):
        return f"DocumentChunk(doc={self.document_name}, chunk={self.chunk_index})"


class RAGService:
    """
    RAG Service for document retrieval and processing.
    Uses Azure AI Search for efficient vector similarity search.
    """

    def __init__(self):
        """Initialize RAG service."""
        self.openai_service = get_azure_openai_service()
        self.embedding_dim: int = 1536  # Default for text-embedding-ada-002
        self._documents_path = Path(settings.DOCUMENTS_PATH)

        # Initialize Azure AI Search clients
        self._search_client = None
        self._index_client = None
        self._initialize_search_clients()

        # Create index if it doesn't exist
        self._create_index_if_not_exists()

        # Index documents if available
        if self._documents_path.exists():
            self.index_documents()

        logger.info("RAG Service initialized")

    def _initialize_search_clients(self) -> None:
        """Initialize Azure AI Search clients."""
        if not settings.AZURE_SEARCH_ENDPOINT or not settings.AZURE_SEARCH_KEY:
            raise ValueError("Azure AI Search endpoint and key must be configured")

        credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        self._search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX_NAME,
            credential=credential
        )
        self._index_client = SearchIndexClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            credential=credential
        )

    def _create_index_if_not_exists(self) -> None:
        """Create Azure AI Search index if it doesn't exist."""
        try:
            # Check if index exists
            self._index_client.get_index(settings.AZURE_SEARCH_INDEX_NAME)
            logger.info(f"Index {settings.AZURE_SEARCH_INDEX_NAME} already exists")
        except Exception:
            # Create the index
            fields = [
                SearchField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True
                ),
                SearchField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True
                ),
                SearchField(
                    name="document_name",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True
                ),
                SearchField(
                    name="chunk_index",
                    type=SearchFieldDataType.Int32,
                    filterable=True
                ),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=self.embedding_dim,
                    vector_search_profile_name="my-vector-profile"
                )
            ]

            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="my-vector-profile",
                        algorithm_configuration_name="my-hnsw-config"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="my-hnsw-config"
                    )
                ]
            )

            index = SearchIndex(
                name=settings.AZURE_SEARCH_INDEX_NAME,
                fields=fields,
                vector_search=vector_search
            )

            self._index_client.create_index(index)
            logger.info(f"Created index {settings.AZURE_SEARCH_INDEX_NAME}")

    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)

            # Try to break at sentence or word boundary
            if end < text_length:
                # Look for sentence boundary
                for boundary in ['. ', '.\n', '! ', '? ', '\n\n']:
                    last_boundary = text.rfind(boundary, start, end)
                    if last_boundary > start + chunk_size // 2:
                        end = last_boundary + len(boundary)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            next_start = end - overlap
            # Ensure we always make progress
            if next_start <= start:
                start = end
            else:
                start = next_start

        return chunks

    def index_documents(self) -> int:
        """
        Index all documents in the documents directory.

        Returns:
            Number of chunks indexed
        """
        logger.info("Indexing documents...")
        documents_to_index = []

        # Process all text files in documents directory
        for doc_path in self._documents_path.glob("*.txt"):
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    content = f.read()

                text_chunks = self._chunk_text(content)
                for i, chunk_text in enumerate(text_chunks):
                    chunk = DocumentChunk(
                        content=chunk_text,
                        document_name=doc_path.name,
                        chunk_index=i
                    )

                    # Generate embedding for the chunk
                    embedding = self.openai_service.get_single_embedding(chunk_text)

                    # Prepare document for Azure AI Search
                    document = {
                        "id": chunk.id,
                        "content": chunk_text,
                        "document_name": doc_path.name,
                        "chunk_index": i,
                        "content_vector": embedding
                    }
                    documents_to_index.append(document)

                logger.info(f"Processed {doc_path.name}: {len(text_chunks)} chunks")

            except Exception as e:
                logger.error(f"Error processing {doc_path}: {e}")

        if not documents_to_index:
            logger.warning("No documents found to index")
            return 0

        # Upload documents to Azure AI Search in batches
        batch_size = 1000
        total_indexed = 0

        for i in range(0, len(documents_to_index), batch_size):
            batch = documents_to_index[i:i + batch_size]
            try:
                result = self._search_client.upload_documents(documents=batch)
                successful = sum(1 for r in result if r.succeeded)
                total_indexed += successful
                logger.info(f"Indexed batch {i//batch_size + 1}: {successful}/{len(batch)} documents")
            except Exception as e:
                logger.error(f"Error indexing batch {i//batch_size + 1}: {e}")

        logger.info(f"Indexed {total_indexed} chunks from documents")
        return total_indexed

    def search(
        self,
        query: str,
        top_k: int = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for relevant document chunks.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (chunk, similarity_score) tuples
        """
        top_k = top_k or settings.TOP_K_RESULTS

        # Generate query embedding
        query_embedding = self.openai_service.get_single_embedding(query)

        # Perform vector search
        try:
            results = self._search_client.search(
                search_text="",  # Empty text search, using only vectors
                vector_queries=[{
                    "vector": query_embedding,
                    "k": top_k,
                    "fields": "content_vector"
                }],
                select=["id", "content", "document_name", "chunk_index"],
                top=top_k
            )

            search_results = []
            for result in results:
                score = result.get("@search.score", 0.0)
                if score >= settings.SIMILARITY_THRESHOLD:
                    chunk = DocumentChunk(
                        content=result["content"],
                        document_name=result["document_name"],
                        chunk_index=result["chunk_index"],
                        id=result["id"]
                    )
                    search_results.append((chunk, float(score)))

            logger.info(f"Found {len(search_results)} relevant chunks for query")
            return search_results

        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return []

    def get_context_for_query(self, query: str) -> Tuple[str, List[str]]:
        """
        Get relevant context and sources for a query.

        Args:
            query: User query

        Returns:
            Tuple of (context_string, source_list)
        """
        results = self.search(query)

        if not results:
            return "", []

        # Build context from retrieved chunks
        context_parts = []
        sources = set()

        for chunk, score in results:
            context_parts.append(f"[From {chunk.document_name}]:\n{chunk.content}")
            sources.add(chunk.document_name)

        context = "\n\n---\n\n".join(context_parts)
        return context, list(sources)


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get or create the RAG service singleton.

    Returns:
        RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
