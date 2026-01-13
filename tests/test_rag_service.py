"""
Unit tests for the RAG Service.
Tests document processing, indexing, and search functionality.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.rag_service import RAGService, DocumentChunk, get_rag_service
from app.core.config import settings


class TestDocumentChunk:
    """Tests for DocumentChunk class."""
    
    def test_document_chunk_creation(self):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            content="This is a test document chunk.",
            document_name="test.txt",
            chunk_index=0
        )
        
        assert chunk.content == "This is a test document chunk."
        assert chunk.document_name == "test.txt"
        assert chunk.chunk_index == 0
    
    def test_document_chunk_repr(self):
        """Test document chunk string representation."""
        chunk = DocumentChunk(
            content="Test content",
            document_name="test.txt",
            chunk_index=5
        )
        
        repr_str = repr(chunk)
        assert "test.txt" in repr_str
        assert "5" in repr_str


class TestRAGService:
    """Tests for RAG Service functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        settings.DEMO_MODE = True
        # Reset singleton for each test
        import app.services.rag_service as rag_module
        rag_module._rag_service = None
        yield
        # Cleanup
        rag_module._rag_service = None
    
    def test_rag_service_initialization(self):
        """Test RAG service initializes correctly."""
        rag = get_rag_service()
        
        assert rag is not None
        assert rag.index is not None
        assert isinstance(rag.chunks, list)
    
    def test_get_rag_service_singleton(self):
        """Test that get_rag_service returns singleton."""
        rag1 = get_rag_service()
        rag2 = get_rag_service()
        
        assert rag1 is rag2
    
    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        settings.DEMO_MODE = True
        rag = RAGService()
        
        text = "This is a test. " * 100  # Create long text
        chunks = rag._chunk_text(text, chunk_size=100, overlap=10)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 100 + 10  # Allow for overlap
    
    def test_chunk_text_short_text(self):
        """Test chunking short text that doesn't need splitting."""
        settings.DEMO_MODE = True
        rag = RAGService()
        
        text = "Short text."
        chunks = rag._chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == "Short text."
    
    def test_search_empty_index(self):
        """Test search with empty index."""
        settings.DEMO_MODE = True
        rag = RAGService()
        
        # Reset index
        rag.index.reset()
        rag.chunks = []
        
        results = rag.search("test query")
        
        assert results == []
    
    def test_search_with_results(self):
        """Test search returns relevant results."""
        settings.DEMO_MODE = True
        rag = get_rag_service()
        
        # First index some documents
        num_chunks = rag.index_documents()
        
        # Should have indexed some chunks
        assert num_chunks > 0
        assert len(rag.chunks) > 0
        
        # Search should return results
        results = rag.search("remote work policy")
        
        assert len(results) > 0
        
        # Check result format
        for chunk, score in results:
            assert isinstance(chunk, DocumentChunk)
            assert isinstance(score, float)
            assert 0 <= score <= 1
    
    def test_get_context_for_query(self):
        """Test getting context for a query."""
        settings.DEMO_MODE = True
        rag = get_rag_service()
        
        # Ensure we have indexed documents
        rag.index_documents()
        
        context, sources = rag.get_context_for_query("remote work policy")
        
        # Context should contain information
        assert isinstance(context, str)
        assert isinstance(sources, list)
        
        # Sources should be from the documents
        if sources:
            assert any(".txt" in source for source in sources)


class TestRAGServiceIntegration:
    """Integration tests for RAG service with real document processing."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        settings.DEMO_MODE = True
        import app.services.rag_service as rag_module
        rag_module._rag_service = None
        yield
        rag_module._rag_service = None
    
    def test_index_documents(self):
        """Test indexing documents from the documents directory."""
        settings.DEMO_MODE = True
        rag = get_rag_service()
        
        initial_chunks = len(rag.chunks)
        
        # Index documents
        num_indexed = rag.index_documents()
        
        # Should have indexed new chunks
        assert num_indexed > 0
        assert len(rag.chunks) > initial_chunks
    
    def test_search_company_policy(self):
        """Test searching for company policy information."""
        settings.DEMO_MODE = True
        rag = get_rag_service()
        
        # Ensure documents are indexed
        rag.index_documents()
        
        # Search for policy-related content
        results = rag.search("remote work policy")
        
        assert len(results) > 0
        
        # At least one result should mention remote work
        found_remote_work = False
        for chunk, score in results:
            if "remote" in chunk.content.lower() or "work" in chunk.content.lower():
                found_remote_work = True
                break
        
        assert found_remote_work
    
    def test_search_with_top_k_parameter(self):
        """Test search with custom top_k parameter."""
        settings.DEMO_MODE = True
        rag = get_rag_service()
        
        rag.index_documents()
        
        results = rag.search("company policy", top_k=5)
        
        assert len(results) <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

