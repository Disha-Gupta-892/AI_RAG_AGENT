"""
Test configuration for the AI Agent RAG Backend.
"""
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set demo mode for testing
import os
os.environ["DEMO_MODE"] = "true"
os.environ["DEBUG"] = "true"

