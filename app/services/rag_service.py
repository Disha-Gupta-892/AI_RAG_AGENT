"""
RAG (Retrieval-Augmented Generation) Service.
Handles document processing, embedding storage, and retrieval using Azure AI Search.
"""

import os
import logging
import pickle
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import faiss
from app.core.config import settings
from app.services.azure_openai_service import get_azure_openai_service

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    
    def __init__(self, content: str, document_name: str, chunk_index: int):
        self.content = content
        self.document_name = document_name
        self.chunk_index = chunk_index

    def __repr__(self):
        return f"DocumentChunk(doc={self.document_name}, chunk={self.chunk_index})"


class RAGService:
    """
    RAG Service for document retrieval and processing.
    Uses FAISS for efficient vector similarity search.
    """
    
    def __init__(self):
        """Initialize RAG service."""
        self.openai_service = get_azure_openai_service()
        self.index: Optional[faiss.IndexFlatIP] = None  # Inner product for cosine similarity
        self.chunks: List[DocumentChunk] = []
        self.embedding_dim: int = 1536  # Default for text-embedding-ada-002
        self._index_path = Path(settings.FAISS_INDEX_PATH)
        self._documents_path = Path(settings.DOCUMENTS_PATH)
        
        # Load existing index or create new one
        self._load_or_create_index()
        logger.info("RAG Service initialized")

    def _load_or_create_index(self) -> None:
        """Load existing FAISS index or create a new one."""
        index_file = self._index_path / "index.faiss"
        chunks_file = self._index_path / "chunks.pkl"
        
        if index_file.exists() and chunks_file.exists():
            try:
                self.index = faiss.read_index(str(index_file))
                with open(chunks_file, "rb") as f:
                    self.chunks = pickle.load(f)
                logger.info(f"Loaded existing index with {len(self.chunks)} chunks")
                return
            except Exception as e:
                logger.warning(f"Error loading index: {e}. Creating new index.")
        
        # Create new index
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.chunks = []
        
        # Index documents if available
        if self._documents_path.exists():
            self.index_documents()

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
        new_chunks = []
        
        # Process all text files in documents directory
        for doc_path in self._documents_path.glob("*.txt"):
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                text_chunks = self._chunk_text(content)
                for i, chunk_text in enumerate(text_chunks):
                    new_chunks.append(DocumentChunk(
                        content=chunk_text,
                        document_name=doc_path.name,
                        chunk_index=i
                    ))
                logger.info(f"Processed {doc_path.name}: {len(text_chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {doc_path}: {e}")
        
        if not new_chunks:
            logger.warning("No documents found to index")
            return 0
        
        # Generate embeddings for all chunks
        chunk_texts = [chunk.content for chunk in new_chunks]
        embeddings = self.openai_service.get_embeddings(chunk_texts)
        
        # Normalize embeddings for cosine similarity
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        self.index.add(embeddings_array)
        self.chunks.extend(new_chunks)
        
        # Save index
        self._save_index()
        
        logger.info(f"Indexed {len(new_chunks)} chunks from documents")
        return len(new_chunks)

    def _save_index(self) -> None:
        """Save FAISS index and chunks to disk."""
        self._index_path.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(self._index_path / "index.faiss"))
        with open(self._index_path / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        
        logger.info("Index saved to disk")

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
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        top_k = top_k or settings.TOP_K_RESULTS
        top_k = min(top_k, self.index.ntotal)  # Can't retrieve more than available
        
        # Generate query embedding
        query_embedding = self.openai_service.get_single_embedding(query)
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        scores, indices = self.index.search(query_array, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score >= settings.SIMILARITY_THRESHOLD:
                results.append((self.chunks[idx], float(score)))
        
        logger.info(f"Found {len(results)} relevant chunks for query")
        return results

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
