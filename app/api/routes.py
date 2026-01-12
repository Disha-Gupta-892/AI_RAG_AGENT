"""
API Routes for the AI Agent application.
Defines all HTTP endpoints for the FastAPI application.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import AskRequest, AskResponse, HealthResponse
from app.services.agent_service import get_agent_service, AgentService
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns application status and version information.
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION
    )


@router.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask(
    request: AskRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Main endpoint for querying the AI Agent.
    
    The agent will:
    1. Analyze the query to determine if it needs document retrieval
    2. Either answer directly using the LLM or retrieve relevant documents first
    3. Return a structured response with sources (if applicable)
    
    Args:
        request: AskRequest containing the query and optional session_id
        
    Returns:
        AskResponse with answer, sources, and metadata
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        response = await agent_service.process_query(
            query=request.query,
            session_id=request.session_id
        )
        
        logger.info(f"Query processed successfully. Type: {response.query_type}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/reindex", tags=["Admin"])
async def reindex_documents():
    """
    Trigger re-indexing of all documents.
    Use this after adding new documents to the documents directory.
    
    Returns:
        Number of chunks indexed
    """
    try:
        from app.services.rag_service import get_rag_service
        rag_service = get_rag_service()
        
        # Clear existing index
        rag_service.index.reset()
        rag_service.chunks = []
        
        # Re-index documents
        num_chunks = rag_service.index_documents()
        
        return {"message": f"Successfully indexed {num_chunks} document chunks"}
        
    except Exception as e:
        logger.error(f"Error re-indexing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error re-indexing documents: {str(e)}"
        )


@router.delete("/session/{session_id}", tags=["Session"])
async def clear_session(session_id: str):
    """
    Clear a specific session's conversation history.
    
    Args:
        session_id: The session ID to clear
        
    Returns:
        Status message
    """
    try:
        from app.services.session_service import get_session_service
        session_service = get_session_service()
        
        if session_service.clear_session(session_id):
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )
