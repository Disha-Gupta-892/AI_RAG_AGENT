import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_imports")

try:
    logger.info("Importing fastapi...")
    import fastapi
    logger.info("Importing pydantic...")
    import pydantic
    logger.info("Importing numpy...")
    import numpy
    logger.info("Importing faiss...")
    import faiss
    logger.info("Importing openai...")
    import openai
    logger.info("Importing langchain...")
    import langchain
    logger.info("All base imports successful")
    
    logger.info("Importing app modules...")
    from app.core.config import settings
    logger.info("Config imported")
    from app.services.rag_service import get_rag_service
    logger.info("RAG service imported")
    from app.services.agent_service import get_agent_service
    logger.info("Agent service imported")
    
    logger.info("All imports successful!")
except Exception as e:
    logger.error(f"Import failed: {e}", exc_info=True)
