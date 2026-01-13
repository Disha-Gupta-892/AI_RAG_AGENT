"""
Integration tests for the API endpoints.
Tests all FastAPI routes and request/response handling.
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Reset singletons
    import app.services.session_service as session_module
    import app.services.rag_service as rag_module
    import app.services.agent_service as agent_module
    import app.services.azure_openai_service as azure_module
    
    session_module._session_service = None
    rag_module._rag_service = None
    agent_module._agent_service = None
    azure_module._azure_openai_service = None
    
    yield
    
    # Cleanup after test
    session_module._session_service = None
    rag_module._rag_service = None
    agent_module._agent_service = None
    azure_module._azure_openai_service = None


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
    
    def test_health_check_content_type(self, client):
        """Test health check returns JSON content."""
        response = client.get("/api/v1/health")
        
        assert response.headers["content-type"] == "application/json"


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/api")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI Agent RAG Backend"
        assert data["version"] == "1.0.0"
        assert "docs_url" in data
        assert "health_check" in data


class TestAskEndpoint:
    """Tests for the main /ask endpoint."""
    
    def test_ask_with_valid_query(self, client):
        """Test asking a question about company policies."""
        response = client.post(
            "/api/v1/ask",
            json={"query": "What is the remote work policy?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "query_type" in data
        assert "session_id" in data
        assert "timestamp" in data
        
        # Should use RAG for policy questions
        assert data["query_type"] in ["rag", "direct"]
    
    def test_ask_with_session_id_new(self, client):
        """Test asking with a new session ID creates session."""
        session_id = "test-session-123"
        response = client.post(
            "/api/v1/ask",
            json={
                "query": "What is the PTO policy?",
                "session_id": session_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # A new session is created since provided session_id doesn't exist
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0
    
    def test_ask_maintains_conversation(self, client):
        """Test that conversation history is maintained."""
        # First message - will create a session
        response1 = client.post(
            "/api/v1/ask",
            json={"query": "What is the remote work policy?"}
        )
        assert response1.status_code == 200
        
        session_id = response1.json()["session_id"]
        
        # Second message in same session
        response2 = client.post(
            "/api/v1/ask",
            json={
                "query": "How many days can I work remotely?",
                "session_id": session_id
            }
        )
        assert response2.status_code == 200
        
        # Both should use same session
        assert response1.json()["session_id"] == response2.json()["session_id"] == session_id
    
    def test_ask_with_empty_query(self, client):
        """Test asking with empty query returns error."""
        response = client.post(
            "/api/v1/ask",
            json={"query": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_ask_with_missing_query(self, client):
        """Test asking without query parameter."""
        response = client.post(
            "/api/v1/ask",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_ask_with_general_knowledge_question(self, client):
        """Test asking a general knowledge question."""
        response = client.post(
            "/api/v1/ask",
            json={"query": "What is the capital of France?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 0
    
    def test_ask_with_product_question(self, client):
        """Test asking about products."""
        response = client.post(
            "/api/v1/ask",
            json={"query": "What are the features of CloudSync Pro?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 0


class TestReindexEndpoint:
    """Tests for the document reindexing endpoint."""
    
    def test_reindex_documents(self, client):
        """Test re-indexing all documents."""
        response = client.post("/api/v1/reindex")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Successfully indexed" in data["message"]
        assert "document chunks" in data["message"]


class TestSessionEndpoint:
    """Tests for session management endpoints."""
    
    def test_create_session(self, client):
        """Test that asking a question creates a session."""
        response = client.post(
            "/api/v1/ask",
            json={"query": "Test question"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0
    
    def test_clear_session(self, client):
        """Test clearing a session."""
        # First create a session
        response = client.post(
            "/api/v1/ask",
            json={"query": "Test question"}
        )
        session_id = response.json()["session_id"]
        
        # Clear the session
        clear_response = client.delete(f"/api/v1/session/{session_id}")
        
        assert clear_response.status_code == 200
        data = clear_response.json()
        assert f"Session {session_id} cleared successfully" in data["message"]
    
    def test_clear_nonexistent_session(self, client):
        """Test clearing a non-existent session returns 404."""
        response = client.delete("/api/v1/session/nonexistent-session-id")
        
        assert response.status_code == 404


class TestFrontendEndpoints:
    """Tests for frontend-related endpoints."""
    
    def test_frontend_served(self, client):
        """Test frontend index is served."""
        response = client.get("/")
        
        # Should return either frontend HTML or API info
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

