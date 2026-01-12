"""
Session Management Service.
Provides in-memory session storage for conversation history.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Lock
from app.core.config import settings
from app.models.schemas import SessionData, SessionMessage

logger = logging.getLogger(__name__)


class SessionService:
    """
    In-memory session management service.
    Stores conversation history for maintaining context across queries.
    """
    
    def __init__(self):
        """Initialize the session store."""
        self._sessions: Dict[str, SessionData] = {}
        self._lock = Lock()
        self._max_history = settings.MAX_SESSION_HISTORY
        self._timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        logger.info("Session Service initialized")

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """
        Get existing session or create a new one.
        
        Args:
            session_id: Optional existing session ID
            
        Returns:
            Valid session ID
        """
        with self._lock:
            # Clean up expired sessions periodically
            self._cleanup_expired_sessions()
            
            if session_id and session_id in self._sessions:
                # Update last accessed time
                self._sessions[session_id].last_accessed = datetime.utcnow()
                return session_id
            
            # Create new session
            new_session_id = str(uuid.uuid4())
            self._sessions[new_session_id] = SessionData(
                session_id=new_session_id,
                messages=[],
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow()
            )
            logger.info(f"Created new session: {new_session_id}")
            return new_session_id

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to session history.
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        with self._lock:
            if session_id not in self._sessions:
                logger.warning(f"Session not found: {session_id}")
                return
            
            session = self._sessions[session_id]
            message = SessionMessage(
                role=role,
                content=content,
                timestamp=datetime.utcnow()
            )
            session.messages.append(message)
            
            # Trim history if exceeds max limit
            if len(session.messages) > self._max_history * 2:
                session.messages = session.messages[-self._max_history * 2:]
            
            session.last_accessed = datetime.utcnow()

    def get_conversation_history(self, session_id: str) -> List[dict]:
        """
        Get conversation history formatted for LLM.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries
        """
        with self._lock:
            if session_id not in self._sessions:
                return []
            
            session = self._sessions[session_id]
            return [
                {"role": msg.role, "content": msg.content}
                for msg in session.messages[-self._max_history * 2:]
            ]

    def clear_session(self, session_id: str) -> bool:
        """
        Clear a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was cleared, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Cleared session: {session_id}")
                return True
            return False

    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions based on timeout."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=self._timeout_minutes)
        expired_sessions = [
            sid for sid, session in self._sessions.items()
            if session.last_accessed < cutoff_time
        ]
        for sid in expired_sessions:
            del self._sessions[sid]
            logger.debug(f"Cleaned up expired session: {sid}")


# Singleton instance
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """
    Get or create the session service singleton.
    
    Returns:
        SessionService instance
    """
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
