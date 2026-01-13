import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Importing main.app...")
    from main import app
    print("Import successful!")
except Exception as e:
    print(f"FAILED to import main.app: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
