from typing import List, Dict, Tuple
import chromadb
from chromadb.config import Settings
import os


def create_or_load_chroma_db(persist_dir: str = "vector_store") -> chromadb.Client:
    """
    Create or load a Chroma DB instance with persistent storage.
    
    Args:
        persist_dir: Path where Chroma will store its data.
    
    Returns:
        Chroma client ready for indexing/retrieval.
    
    Why Chroma:
        - Simple API for embedding storage + retrieval.
        - Built-in metadata filtering.
        - Persistent storage on disk.
    """
    os.makedirs(persist_dir, exist_ok=True)
    settings = Settings(
        is_persistent=True,
        persist_directory=persist_dir,
        anonymized_telemetry=False,
    )
    client = chromadb.Client(settings)
    return client


def index_chunks_to_chroma(
    chunks: List[Dict],
    embeddings: List[List[float]],
    collection_name: str = "documents",
    persist_dir: str = "vector_store",
) -> chromadb.Collection:
    """
    Index chunks with their embeddings into a Chroma collection.
    
    Args:
        chunks: List of dicts with "id", "text", "meta".
        embeddings: List of embedding vectors (same length as chunks).
        collection_name: Name of the collection in Chroma.
        persist_dir: Directory for persistent storage.
    
    Returns:
        Chroma collection object (useful for later retrieval).
    
    Common mistakes to avoid:
        - Mismatch between len(chunks) and len(embeddings).
        - Forgetting to include metadata; makes filtering later impossible.
        - Not persisting; index will be lost on restart.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Chunk count ({len(chunks)}) must match embedding count ({len(embeddings)})"
        )
    
    client = create_or_load_chroma_db(persist_dir)

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    
    # Add documents with embeddings and metadata
    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [c["meta"] for c in chunks]
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    
    print(f"Indexed {len(chunks)} chunks into Chroma collection '{collection_name}'")
    return collection


def retrieve_similar_chunks(
    query_text: str,
    query_embedding: List[float],
    collection_name: str = "documents",
    persist_dir: str = "vector_store",
    top_k: int = 5,
) -> List[Tuple[str, float, Dict]]:
    """
    Retrieve top-k chunks similar to a query.
    
    Args:
        query_text: The search query (for context/logging).
        query_embedding: Embedding vector of the query.
        collection_name: Name of the collection.
        persist_dir: Directory with persistent storage.
        top_k: Number of results to return.
    
    Returns:
        List of tuples: (chunk_text, similarity_score, metadata)
    """
    client = create_or_load_chroma_db(persist_dir)
    collection = client.get_collection(name=collection_name)
    
    # Query the collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )
    
    # Chroma returns distances; convert to similarity (1 - distance for cosine)
    retrieved = []
    if results["documents"] and len(results["documents"]) > 0:
        for doc, dist, meta in zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0],
        ):
            similarity = 1 - dist  # For cosine distance
            retrieved.append((doc, similarity, meta))
    
    return retrieved
