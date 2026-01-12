"""
Pydantic schemas for API request and response models.
Defines the data structures used across the application.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class QueryType(str, Enum):
    """Enum for query classification types."""
    DIRECT = "direct"  # Can be answered directly by LLM
    RAG = "rag"  # Requires document retrieval


class AskRequest(BaseModel):
    """
    Request schema for the /ask endpoint.
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question or query"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for conversation continuity"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the company's remote work policy?",
                "session_id": "user_123_session_abc"
            }
        }


class DocumentSource(BaseModel):
    """
    Schema for document source information.
    """
    document_name: str = Field(..., description="Name of the source document")
    chunk_content: str = Field(..., description="Relevant content from the document")
    similarity_score: float = Field(..., description="Similarity score (0-1)")


class AskResponse(BaseModel):
    """
    Response schema for the /ask endpoint.
    """
    answer: str = Field(..., description="The generated answer")
    sources: List[str] = Field(
        default_factory=list,
        description="List of source document names used"
    )
    query_type: QueryType = Field(..., description="Type of query processing used")
    session_id: str = Field(..., description="Session ID for this conversation")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "According to our company policy, employees can work remotely up to 3 days per week...",
                "sources": ["company_policies.txt", "hr_guidelines.txt"],
                "query_type": "rag",
                "session_id": "user_123_session_abc",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """
    Response schema for health check endpoint.
    """
    status: str = Field(..., description="Application health status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )


class SessionMessage(BaseModel):
    """
    Schema for a single message in session history.
    """
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )


class SessionData(BaseModel):
    """
    Schema for session data storage.
    """
    session_id: str = Field(..., description="Unique session identifier")
    messages: List[SessionMessage] = Field(
        default_factory=list,
        description="Conversation history"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session creation timestamp"
    )
    last_accessed: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last access timestamp"
    )
