import argparse
from pathlib import Path
from src import embedding, generation, ingestion, retrieval


def build_rag_index(pdf_path: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Full pipeline: ingest PDF -> chunk -> embed -> index.
    
    Args:
        pdf_path: Path to PDF file.
        chunk_size: Characters per chunk.
        overlap: Characters of overlap between chunks.
    
    Returns:
        Collection name if successful.
    """
    # Step 1: Ingest & chunk
    print(f"[1/3] Ingesting {pdf_path}...")
    chunks = ingestion.ingest_pdf(pdf_path, chunk_size=chunk_size, overlap=overlap)
    print(f"  ✓ Created {len(chunks)} chunks")
    
    # Step 2: Embed
    print(f"[2/3] Embedding {len(chunks)} chunks...")
    texts_to_embed = [c["text"] for c in chunks]
    embeddings_list = embedding.get_embeddings(texts_to_embed)
    print(f"  ✓ Generated embeddings (dim={len(embeddings_list[0])})")
    
    # Step 3: Index
    print(f"[3/3] Indexing into Chroma...")
    collection_name = "documents"
    retrieval.index_chunks_to_chroma(
        chunks=chunks,
        embeddings=embeddings_list,
        collection_name=collection_name,
        persist_dir="vector_store",
    )
    print(f"  ✓ Index saved to vector_store/")
    
    return collection_name


def ask_rag(question: str, top_k: int = 5):
    result = generation.answer_question(question=question, top_k=top_k)
    print("\nQuestion:")
    print(result["question"])
    print("\nAnswer (grounded):")
    print(result["answer"])
    print("\nRetrieved contexts:")
    for idx, (_, sim, meta) in enumerate(result["contexts"], start=1):
        print(f"[{idx}] similarity={sim:.4f} source={meta.get('source')} page={meta.get('page')}")


def main():
    parser = argparse.ArgumentParser(description="RAG pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_index = subparsers.add_parser("index", help="Build index from a PDF")
    p_index.add_argument("pdf_path", type=str, help="Path to PDF file")
    p_index.add_argument("--chunk_size", type=int, default=1000, help="Chunk size in characters")
    p_index.add_argument("--overlap", type=int, default=200, help="Chunk overlap in characters")

    p_ask = subparsers.add_parser("ask", help="Ask a question over indexed docs")
    p_ask.add_argument("question", type=str, help="Question to ask")
    p_ask.add_argument("--top_k", type=int, default=5, help="Number of contexts to retrieve")

    args = parser.parse_args()

    if args.command == "index":
        pdf = Path(args.pdf_path)
        if not pdf.exists():
            print(f"❌ File not found: {pdf}")
            return

        build_rag_index(str(pdf), chunk_size=args.chunk_size, overlap=args.overlap)
        print("\n✅ RAG index built successfully!")
        return

    if args.command == "ask":
        ask_rag(args.question, top_k=args.top_k)
        return

if __name__ == "__main__":
    main()

