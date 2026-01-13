"""
RAG (Retrieval-Augmented Generation) Service.
Handles document processing and retrieval using Azure AI Search.
"""

import logging
import uuid
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchIndexCustomEntityComponent,
)
from app.core.config import settings
from app.services.azure_openai_service import get_azure_openai_service

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    
    def __init__(self, content: str, document_name: str, chunk_index: int, id: str = None):
        self.id = id or str(uuid.uuid4())
        self.content = content
        self.document_name = document_name
        self.chunk_index = chunk_index

    def __repr__(self):
        return f"DocumentChunk(doc={self.document_name}, chunk={self.chunk_index})"


class RAGService:
    """
    RAG Service for document retrieval and processing.
    Uses Azure AI Search for vector similarity search.
    """
    
    def __init__(self):
        """Initialize RAG service."""
        self.openai_service = get_azure_openai_service()
        self.endpoint = settings.AZURE_SEARCH_SERVICE_ENDPOINT
        self.key = settings.AZURE_SEARCH_ADMIN_KEY
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        self._documents_path = Path(settings.DOCUMENTS_PATH)
        
        if self.endpoint and self.key:
            self.search_client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=AzureKeyCredential(self.key)
            )
            self.index_client = SearchIndexClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
            # Ensure index exists
            self._ensure_index_exists()
        else:
            logger.warning("Azure AI Search credentials not provided. RAG service will be limited.")
            self.search_client = None
            self.index_client = None

        logger.info("RAG Service initialized with Azure AI Search")

    def _ensure_index_exists(self) -> None:
        """Create the Azure AI Search index if it doesn't already exist."""
        try:
            self.index_client.get_index(self.index_name)
            logger.info(f"Index '{self.index_name}' already exists.")
        except Exception:
            logger.info(f"Index '{self.index_name}' not found. Creating...")
            
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SimpleField(name="document_name", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536, # Default for ada-002
                    vector_search_profile_name="myHnswProfile"
                )
            ]

            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(name="myHnsw")
                ],
                profiles=[
                    VectorSearchProfile(
                        name="myHnswProfile",
                        algorithm_configuration_name="myHnsw"
                    )
                ]
            )

            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            self.index_client.create_index(index)
            logger.info(f"Successfully created index '{self.index_name}'")

    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks."""
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            if end < text_length:
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
            start = end - overlap
        return chunks

    def index_documents(self) -> int:
        """Index all documents in the documents directory to Azure AI Search."""
        if not self.search_client:
            logger.error("Search client not initialized. Cannot index documents.")
            return 0

        logger.info("Indexing documents to Azure AI Search...")
        documents_to_upload = []
        
        for doc_path in self._documents_path.glob("*.txt"):
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                text_chunks = self._chunk_text(content)
                chunk_texts = [c for c in text_chunks]
                embeddings = self.openai_service.get_embeddings(chunk_texts)
                
                for i, (chunk_text, embedding) in enumerate(zip(text_chunks, embeddings)):
                    documents_to_upload.append({
                        "id": str(uuid.uuid4()),
                        "content": chunk_text,
                        "document_name": doc_path.name,
                        "chunk_index": i,
                        "content_vector": embedding
                    })
                
                logger.info(f"Prepared {doc_path.name}: {len(text_chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {doc_path}: {e}")
        
        if not documents_to_upload:
            logger.warning("No documents found to index")
            return 0
        
        # Upload in batches
        batch_size = 100
        total_uploaded = 0
        for i in range(0, len(documents_to_upload), batch_size):
            batch = documents_to_upload[i:i + batch_size]
            self.search_client.upload_documents(documents=batch)
            total_uploaded += len(batch)
            
        logger.info(f"Successfully uploaded {total_uploaded} chunks to Azure AI Search")
        return total_uploaded

    def search(
        self, 
        query: str, 
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks using vector search."""
        if not self.search_client:
            logger.warning("Search client not initialized.")
            return []
        
        top_k = top_k or settings.TOP_K_RESULTS
        query_vector = self.openai_service.get_single_embedding(query)
        
        from azure.search.documents.models import VectorizedQuery
        vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector")
        
        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["content", "document_name", "chunk_index"],
            top=top_k
        )
        
        return list(results)

    def get_context_for_query(self, query: str) -> Tuple[str, List[str]]:
        """Get relevant context and sources for a query."""
        results = self.search(query)
        
        if not results:
            return "", []
        
        context_parts = []
        sources = set()
        
        for result in results:
            context_parts.append(f"[From {result['document_name']}]:\n{result['content']}")
            sources.add(result['document_name'])
        
        context = "\n\n---\n\n".join(context_parts)
        return context, list(sources)


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
