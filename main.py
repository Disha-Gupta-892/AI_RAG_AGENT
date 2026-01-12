"""
Main FastAPI Application Entry Point.
Configures and runs the AI Agent RAG Backend application.
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get the frontend directory path
FRONTEND_DIR = Path(__file__).parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes services on startup and cleans up on shutdown.
    """
    # Startup
    logger.info("Starting AI Agent RAG Backend...")
    
    # Initialize services (lazy loading, but we can pre-warm here)
    try:
        from app.services.rag_service import get_rag_service
        from app.services.agent_service import get_agent_service
        
        # Pre-initialize services
        rag_service = get_rag_service()
        agent_service = get_agent_service()
        
        logger.info(f"RAG Service initialized with {len(rag_service.chunks)} document chunks")
        logger.info("AI Agent Service initialized")
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent RAG Backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## AI Agent RAG Backend
    
    An intelligent AI Agent that can:
    - Answer questions directly using Azure OpenAI
    - Retrieve and use relevant documents (RAG) when needed
    - Maintain conversation context across sessions
    
    ### Features
    - **Intelligent Query Routing**: Automatically decides whether to use RAG or direct LLM response
    - **Document Retrieval**: Uses FAISS for efficient vector similarity search
    - **Session Memory**: Maintains conversation history for context
    - **Tool Calling**: Uses OpenAI function calling for smart decision making
    
    ### Endpoints
    - `POST /ask` - Main endpoint for querying the agent
    - `GET /health` - Health check endpoint
    - `POST /reindex` - Re-index documents
    - `DELETE /session/{session_id}` - Clear session history
    """,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

# Mount static files for frontend (CSS, JS)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# Serve frontend
@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve the frontend chat interface."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/v1/health",
        "message": "Frontend not found. Access /docs for API documentation."
    }


# API info endpoint
@app.get("/api", tags=["Root"])
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
