# =========================================================
# RAG METRICS – FINAL SINGLE FILE (RUN DIRECTLY)
# =========================================================

import os
import pickle
from typing import List, Dict, Set

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


# =========================================================
# CONFIG
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db")

INDEX_PATH = os.path.join(VECTOR_DB_DIR, "index.faiss")
TEXTS_PATH = os.path.join(VECTOR_DB_DIR, "texts.pkl")

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5
SIM_THRESHOLD = 0.70   # concept similarity threshold


# =========================================================
# LOAD RAG INDEX
# =========================================================

if not os.path.exists(INDEX_PATH) or not os.path.exists(TEXTS_PATH):
    raise RuntimeError("FAISS index or texts not found. Run build_index.py first.")

embedder = SentenceTransformer(EMBED_MODEL)
index = faiss.read_index(INDEX_PATH)

with open(TEXTS_PATH, "rb") as f:
    TEXT_CHUNKS: List[Dict] = pickle.load(f)


# =========================================================
# SEMANTIC RETRIEVAL
# =========================================================

def retrieve_chunks(query: str, top_k: int = TOP_K) -> List[Dict]:
    vec = embedder.encode([query]).astype("float32")
    _, idxs = index.search(vec, top_k)
    return [TEXT_CHUNKS[i] for i in idxs[0] if 0 <= i < len(TEXT_CHUNKS)]


# =========================================================
# CONCEPT EXTRACTION (EMBEDDING-BASED)
# =========================================================

def extract_concepts(text: str) -> Set[str]:
    tokens = (
        text.lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace("(", " ")
        .replace(")", " ")
        .split()
    )

    tokens = [t for t in tokens if len(t) > 4]
    if not tokens:
        return set()

    vecs = embedder.encode(tokens, normalize_embeddings=True)

    concepts: List[str] = []
    concept_vecs: List[np.ndarray] = []

    for token, vec in zip(tokens, vecs):
        if all(np.dot(vec, v) < SIM_THRESHOLD for v in concept_vecs):
            concepts.append(token)
            concept_vecs.append(vec)

    return set(concepts)


# =========================================================
# HARD NEGATIVE SAMPLING
# =========================================================

def hard_negatives(positives: List[Dict]) -> List[Dict]:
    pos_text = " ".join(p["text"] for p in positives)
    pos_vec = embedder.encode([pos_text], normalize_embeddings=True)

    all_vecs = embedder.encode(
        [c["text"] for c in TEXT_CHUNKS],
        normalize_embeddings=True,
    )

    sims = np.dot(all_vecs, pos_vec.T).squeeze()
    sorted_ids = np.argsort(-sims)

    negatives = []
    positive_ids = {id(p) for p in positives}

    for idx in sorted_ids:
        chunk = TEXT_CHUNKS[idx]
        if id(chunk) not in positive_ids:
            negatives.append(chunk)
        if len(negatives) >= len(positives):
            break

    return negatives


# =========================================================
# METRICS
# =========================================================

def compute_metrics(gt: Set[str], retrieved: Set[str]) -> Dict[str, float]:
    tp = len(gt & retrieved)
    fp = len(retrieved - gt)
    fn = len(gt - retrieved)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }


# =========================================================
# FULL RAG EVALUATION
# =========================================================

def evaluate_rag(query: str, reference_answer: str) -> Dict[str, float]:
    positives = retrieve_chunks(query)
    negatives = hard_negatives(positives)

    retrieved_concepts: Set[str] = set()
    for c in positives + negatives:
        retrieved_concepts |= extract_concepts(c["text"])

    reference_concepts = extract_concepts(reference_answer)

    return compute_metrics(reference_concepts, retrieved_concepts)


# =========================================================
# MAIN – RUN DIRECTLY
# =========================================================

if __name__ == "__main__":
    # Example only for evaluation run
    QUERY = "Java interface abstraction multiple inheritance"
    REFERENCE = (
        "An interface in Java defines abstract methods, supports multiple "
        "inheritance, enables abstraction, and promotes loose coupling."
    )

    metrics = evaluate_rag(QUERY, REFERENCE)

    print("\n📊 RAG METRICS (FINAL & REALISTIC)")
    print("Precision:", metrics["precision"])
    print("Recall   :", metrics["recall"])
    print("F1 Score :", metrics["f1"])
