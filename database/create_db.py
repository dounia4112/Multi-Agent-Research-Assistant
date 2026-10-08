"""Create the research_runs table. The API also does this on startup."""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from database.db import init_db

if __name__ == "__main__":
    load_dotenv()
    init_db()
    print("✓ Table ready")
