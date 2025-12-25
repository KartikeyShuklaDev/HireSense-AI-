import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# API key is taken from environment by google-genai, but we keep this for reference
GEMINI_API_KEY = os.getenv("")

BOOKS_DIR = BASE_DIR / "data" / "books"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = VECTOR_DB_DIR / "index.faiss"
TEXTS_PATH = VECTOR_DB_DIR / "texts.pkl"

AUDIO_DIR = BASE_DIR / "data" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
