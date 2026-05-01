#!/usr/bin/env python
"""
Test script: Verify RAG pipeline (ingest -> embed -> index -> retrieve).
Run this after building the index to validate everything works.
"""
from pathlib import Path
from src import embedding, retrieval


def test_retrieval():
    """Test that we can retrieve chunks from Chroma."""
    print("\n=== Testing RAG Retrieval ===\n")
    
    # Verify index exists
    chroma_dir = Path("vector_store")
    if not chroma_dir.exists():
        print("❌ vector_store/ not found. Run: python -m src.main data/BU_HR_Manual_.pdf")
        return False
    
    # Pick a test query
    test_query = "HR policy employee benefits"
    print(f"Test Query: '{test_query}'")
    
    # Embed the query
    query_embedding = embedding.get_embeddings([test_query])[0]
    print(f"Query embedding dim: {len(query_embedding)}")
    
    # Retrieve similar chunks
    results = retrieval.retrieve_similar_chunks(
        query_text=test_query,
        query_embedding=query_embedding,
        collection_name="documents",
        persist_dir="vector_store",
        top_k=3,
    )
    
    if not results:
        print("❌ No results retrieved!")
        return False
    
    print(f"\n✓ Retrieved {len(results)} chunks:\n")
    for i, (chunk_text, similarity, meta) in enumerate(results, 1):
        print(f"[{i}] Similarity: {similarity:.4f} | {meta}")
        print(f"    {chunk_text[:100]}...\n")
    
    print("✅ Retrieval test passed!")
    return True


if __name__ == "__main__":
    success = test_retrieval()
    exit(0 if success else 1)
