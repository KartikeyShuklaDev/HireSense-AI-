import sys
from pathlib import Path

# ensure backend root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import pickle
from typing import List, Dict

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss

from config import BOOKS_DIR, VECTOR_DB_DIR, INDEX_PATH, TEXTS_PATH

MODEL_NAME = "all-MiniLM-L6-v2"


def extract_text_from_pdfs() -> List[Dict]:
    """
    Extract text from all PDFs in data/books.
    Returns list of dicts: { "text": chunk, "source": pdf_filename }.
    """
    chunks: List[Dict] = []

    for pdf_path in BOOKS_DIR.glob("*.pdf"):
        print(f"Reading {pdf_path.name} ...")
        reader = PdfReader(str(pdf_path))
        pages_text = []
        for page in reader.pages:
            try:
                pages_text.append(page.extract_text() or "")
            except Exception as e:
                print(f"Error reading a page in {pdf_path.name}: {e}")
        doc_text = "\n".join(pages_text)
        file_chunks = chunk_text(doc_text, source_name=pdf_path.name)
        chunks.extend(file_chunks)

    print(f"Total chunks extracted from all books: {len(chunks)}")
    return chunks


def chunk_text(
    text: str,
    source_name: str,
    max_chars: int = 800,
    overlap: int = 200,
) -> List[Dict]:
    """
    Break long text into overlapping chunks.
    Each chunk has { "text": ..., "source": source_name }.
    """
    text = text.replace("\r", " ").replace("\n", " ")
    res: List[Dict] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end].strip()
        if chunk:
            res.append({
                "text": chunk,
                "source": source_name,
            })
        if end == n:
            break
        start = end - overlap

    return res


def build_index():
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

    print("Extracting chunks from PDF books (with sources)...")
    chunks = extract_text_from_pdfs()

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    texts = [c["text"] for c in chunks]
    print("Embedding chunks...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    dim = embeddings.shape[1]

    faiss.normalize_L2(embeddings)

    print(f"Creating FAISS index (dim={dim})...")
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    print(f"Saving FAISS index to {INDEX_PATH}")
    faiss.write_index(index, str(INDEX_PATH))

    # Save chunks (text + source) for reference
    print(f"Saving chunk metadata (text + source) to {TEXTS_PATH}")
    with open(TEXTS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print("Index build complete.")


if __name__ == "__main__":
    build_index()
