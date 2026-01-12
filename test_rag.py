
import logging
import sys
from pathlib import Path

# Add the current directory to sys.path
sys.path.append(str(Path(__file__).parent))

from app.services.rag_service import get_rag_service
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_rag():
    print("Initializing RAG Service...")
    settings.DEMO_MODE = True
    rag = get_rag_service()
    
    print(f"RAG Service initialized with {len(rag.chunks)} chunks")
    
    query = "What is the remote work policy?"
    print(f"Searching for: {query}")
    results = rag.search(query)
    
    for chunk, score in results:
        print(f"Score: {score:.4f} | Source: {chunk.document_name}")
        print(f"Content: {chunk.content[:100]}...")
        print("-" * 20)

if __name__ == "__main__":
    test_rag()
