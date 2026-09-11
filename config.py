import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

EMBEDDING_MODEL = "gemini-embedding-001"

LLM_MODEL = "gemini-3.6-flash"

PROJECT_ROOT = Path(__file__).resolve().parent

CHROMA_PATH = str(PROJECT_ROOT / "chroma_db")

COLLECTION_NAME = "company_policies"