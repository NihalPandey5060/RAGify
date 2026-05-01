import os
from typing import List, Tuple
import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
import re
from collections import Counter
from hashlib import blake2b
import math


# Initialize Chroma client
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")
VECTOR_DIM = int(os.getenv("RAG_EMBED_DIM", "384"))


def _get_chroma_client():
    """Get or create Chroma client with persistent storage."""
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    settings = Settings(
        is_persistent=True,
        persist_directory=CHROMA_DB_DIR,
        anonymized_telemetry=False,
    )
    return chromadb.Client(settings)


# ============== Text Processing ==============

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _hash_token(token: str) -> int:
    digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % VECTOR_DIM


def _embed_text(text: str) -> List[float]:
    """Local deterministic embedding (no API calls)."""
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * VECTOR_DIM

    counts = Counter(tokens)
    vector = [0.0] * VECTOR_DIM

    for token, count in counts.items():
        idx = _hash_token(token)
        weight = 1.0 + math.log(count)
        vector[idx] += weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector

    return [value / norm for value in vector]


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    return [_embed_text(text) for text in texts]


# ============== Document Processing ==============

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[dict]:
    """Chunk text with overlap."""
    chunks = []
    chunk_id = 0
    
    pages = text.split("\n\n")  # Split by paragraphs
    for page_idx, page in enumerate(pages, start=1):
        if not page.strip():
            continue
        
        start = 0
        length = len(page)
        while start < length:
            end = min(start + chunk_size, length)
            chunk_text = page[start:end]
            chunks.append({
                "id": f"chunk_{chunk_id}",
                "text": chunk_text,
                "metadata": {"page": page_idx, "chunk_idx": chunk_id}
            })
            chunk_id += 1
            if end == length:
                break
            start = end - overlap
    
    return chunks


# ============== Chroma Operations ==============

def store_document_chunks(chunks: List[dict], user_id: str):
    """Store document chunks in Chroma."""
    client = _get_chroma_client()
    collection_name = f"doc_{user_id}"
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    
    # Create new collection
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Generate embeddings and store
    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    embeddings = get_embeddings(texts)
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    
    return len(chunks)


def retrieve_chunks(query: str, user_id: str, top_k: int = 5) -> List[Tuple[str, float, dict]]:
    """Retrieve relevant chunks for a query."""
    client = _get_chroma_client()
    collection_name = f"doc_{user_id}"
    
    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        return []
    
    query_embedding = _embed_text(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )
    
    retrieved = []
    if results["documents"] and len(results["documents"]) > 0:
        for doc, dist, meta in zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0],
        ):
            similarity = 1 - dist
            retrieved.append((doc, similarity, meta))
    
    return retrieved
