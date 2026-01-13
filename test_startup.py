import logging
import sys
import os

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("test_startup")

# Add current directory to path
sys.path.append(os.getcwd())

def test():
    try:
        logger.info("Testing RAG Service initialization...")
        from app.services.rag_service import get_rag_service
        from app.services.agent_service import get_agent_service
        
        # This will trigger model downloads
        rag_service = get_rag_service()
        logger.info("RAG Service initialized")
        
        agent_service = get_agent_service()
        logger.info("Agent Service initialized")
        
        logger.info("Test complete!")
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}", exc_info=True)

if __name__ == "__main__":
    test()
