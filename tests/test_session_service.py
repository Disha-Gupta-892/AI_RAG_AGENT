"""
Unit tests for the Session Service.
Tests session management and conversation history functionality.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.session_service import SessionService, get_session_service
from app.models.schemas import SessionData, SessionMessage


class TestSessionService:
    """Tests for Session Service functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        # Reset singleton for each test
        import app.services.session_service as session_module
        session_module._session_service = None
        yield
        # Cleanup
        session_module._session_service = None
    
    def test_session_service_initialization(self):
        """Test session service initializes correctly."""
        service = get_session_service()
        
        assert service is not None
        assert isinstance(service._sessions, dict)
        assert service._max_history == 10  # From config
        assert service._timeout_minutes == 60  # From config
    
    def test_get_session_service_singleton(self):
        """Test that get_session_service returns singleton."""
        service1 = get_session_service()
        service2 = get_session_service()
        
        assert service1 is service2
    
    def test_create_new_session(self):
        """Test creating a new session."""
        service = get_session_service()
        
        # Create session without providing ID
        session_id = service.get_or_create_session(None)
        
        assert session_id is not None
        assert len(session_id) > 0
        assert session_id in service._sessions
        
        # Verify session data
        session_data = service._sessions[session_id]
        assert isinstance(session_data, SessionData)
        assert len(session_data.messages) == 0
        assert session_data.session_id == session_id
    
    def test_get_existing_session(self):
        """Test getting an existing session."""
        service = get_session_service()
        
        # Create initial session
        original_id = service.get_or_create_session(None)
        
        # Get same session
        retrieved_id = service.get_or_create_session(original_id)
        
        assert retrieved_id == original_id
    
    def test_get_or_create_session_with_existing_id(self):
        """Test that existing session ID is returned correctly."""
        service = get_session_service()
        
        # First create a session to get a valid session_id
        original_id = service.get_or_create_session(None)
        
        # Now if we provide that existing ID, it should return the same
        retrieved_id = service.get_or_create_session(original_id)
        
        assert retrieved_id == original_id

    def test_add_message_to_session(self):
        """Test adding messages to a session."""
        service = get_session_service()
        
        session_id = service.get_or_create_session(None)
        
        # Add user message
        service.add_message(session_id, "user", "Hello, I need help.")
        
        # Add assistant message
        service.add_message(session_id, "assistant", "Hello! How can I assist you?")
        
        session_data = service._sessions[session_id]
        assert len(session_data.messages) == 2
        
        # Verify message content
        messages = session_data.messages
        assert messages[0].role == "user"
        assert messages[0].content == "Hello, I need help."
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hello! How can I assist you?"
    
    def test_get_conversation_history(self):
        """Test getting conversation history."""
        service = get_session_service()
        
        session_id = service.get_or_create_session(None)
        
        # Add some messages
        service.add_message(session_id, "user", "First question?")
        service.add_message(session_id, "assistant", "First answer.")
        service.add_message(session_id, "user", "Second question?")
        service.add_message(session_id, "assistant", "Second answer.")
        
        # Get history
        history = service.get_conversation_history(session_id)
        
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "First question?"
        assert history[2]["role"] == "user"
        assert history[2]["content"] == "Second question?"
    
    def test_get_history_nonexistent_session(self):
        """Test getting history for non-existent session."""
        service = get_session_service()
        
        history = service.get_conversation_history("nonexistent-session-id")
        
        assert history == []
    
    def test_clear_session(self):
        """Test clearing a session."""
        service = get_session_service()
        
        session_id = service.get_or_create_session(None)
        service.add_message(session_id, "user", "Test message")
        
        # Verify session exists
        assert session_id in service._sessions
        
        # Clear session
        result = service.clear_session(session_id)
        
        assert result is True
        assert session_id not in service._sessions
    
    def test_clear_nonexistent_session(self):
        """Test clearing a non-existent session."""
        service = get_session_service()
        
        result = service.clear_session("nonexistent-session-id")
        
        assert result is False
    
    def test_add_message_to_nonexistent_session(self):
        """Test adding message to non-existent session."""
        service = get_session_service()
        
        # Should not raise exception, just log warning
        service.add_message("nonexistent-session", "user", "Test message")
    
    def test_message_history_limit(self):
        """Test that session history is limited to max history."""
        service = get_session_service()
        
        session_id = service.get_or_create_session(None)
        
        # Add more messages than the limit (max_history * 2 = 20)
        for i in range(25):
            service.add_message(session_id, "user", f"Message {i}")
        
        session_data = service._sessions[session_id]
        
        # Should be limited to max_history * 2
        assert len(session_data.messages) <= 20


class TestSessionData:
    """Tests for SessionData model."""
    
    def test_session_data_creation(self):
        """Test creating session data."""
        session = SessionData(
            session_id="test-session",
            messages=[]
        )
        
        assert session.session_id == "test-session"
        assert session.messages == []
        assert session.created_at is not None
        assert session.last_accessed is not None
    
    def test_session_data_with_messages(self):
        """Test session data with messages."""
        messages = [
            SessionMessage(role="user", content="Hello"),
            SessionMessage(role="assistant", content="Hi there!")
        ]
        
        session = SessionData(
            session_id="test-session",
            messages=messages
        )
        
        assert len(session.messages) == 2


class TestSessionMessage:
    """Tests for SessionMessage model."""
    
    def test_session_message_creation(self):
        """Test creating a session message."""
        message = SessionMessage(
            role="user",
            content="This is a test message."
        )
        
        assert message.role == "user"
        assert message.content == "This is a test message."
        assert message.timestamp is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

