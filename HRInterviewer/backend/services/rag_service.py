import pickle
import random
from functools import lru_cache
from typing import List, Dict, Tuple

import faiss
from sentence_transformers import SentenceTransformer

from config import INDEX_PATH, TEXTS_PATH

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_chunks() -> List[Dict]:
    """
    Load list of dicts:
      { "text": <chunk_text>, "source": <pdf_filename> }
    """
    if not TEXTS_PATH.exists():
        raise RuntimeError(
            f"Texts file not found: {TEXTS_PATH}. Run 'python -m scripts.build_index' first."
        )
    with open(TEXTS_PATH, "rb") as f:
        chunks: List[Dict] = pickle.load(f)
    return chunks


@lru_cache(maxsize=1)
def _load_index():
    if not INDEX_PATH.exists():
        raise RuntimeError(
            f"Index file not found: {INDEX_PATH}. Run 'python -m scripts.build_index' first."
        )
    return faiss.read_index(str(INDEX_PATH))


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def get_relevant_chunks_with_sources(topic: str, top_k: int = 8) -> List[Dict]:
    """
    Search FAISS with topic/question text and return a list of chunk dicts:
      [{ "text": ..., "source": ... }, ...]
    """
    topic = (topic or "").strip()
    if not topic:
        return []

    chunks = _load_chunks()
    index = _load_index()
    model = _load_model()

    query_emb = model.encode([topic])
    faiss.normalize_L2(query_emb)

    distances, indices = index.search(query_emb, top_k)
    idxs = indices[0]

    selected: List[Dict] = []
    for i in idxs:
        if 0 <= i < len(chunks):
            selected.append(chunks[i])

    return selected


def get_relevant_context(topic: str, top_k: int = 8) -> str:
    """
    Backwards-compatible: just return a big context string.
    """
    selected = get_relevant_chunks_with_sources(topic, top_k)
    return "\n\n".join(c["text"] for c in selected)


def get_random_chunks_with_sources(num_chunks: int = 8) -> List[Dict]:
    """
    Randomly sample chunks from ANY data stored in RAG (no topic).
    """
    chunks = _load_chunks()
    if not chunks:
        return []

    k = min(num_chunks, len(chunks))
    indices = random.sample(range(len(chunks)), k=k)
    return [chunks[i] for i in indices]


def get_random_context(num_chunks: int = 8) -> str:
    selected = get_random_chunks_with_sources(num_chunks)
    return "\n\n".join(c["text"] for c in selected)
