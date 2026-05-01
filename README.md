# RAG Project (PDF -> Chroma)

A simple production-style RAG pipeline with:
- PDF ingestion and chunking
- Local deterministic embeddings
- Chroma indexing and retrieval
- Grounded extractive answer generation

## End-to-End Pipeline

1. **Load PDF**: `src/ingestion.py` reads the PDF in `data/` and extracts text page by page.
2. **Chunk text**: The page text is split into overlapping chunks so each chunk keeps nearby context.
3. **Embed chunks**: `src/embedding.py` converts each chunk into a 384-dimensional vector using a local deterministic embedder.
4. **Store vectors**: `src/retrieval.py` writes chunk text, embeddings, and metadata into Chroma inside `vector_store/`.
5. **Retrieve relevant chunks**: A question is embedded with the same embedding function and compared against the stored vectors.
6. **Generate grounded answer**: `src/generation.py` selects the best retrieved sentences and prints a grounded answer with source and page references.

In short, the flow is: PDF -> chunks -> embeddings -> Chroma index -> retrieval -> grounded answer.

## Setup

```powershell
& ".venv/Scripts/python.exe" -m pip install -r requirements.txt
```

## How Indexing & Embedding Works

1. **Ingestion** ([src/ingestion.py](src/ingestion.py)): Reads PDF pages, splits into chunks (default 1000 chars with 200 char overlap)
2. **Embedding** ([src/embedding.py](src/embedding.py)): Each chunk text is converted to a 384-dim vector using a local hash-based embedder:
   - Tokenizes text (lowercase alphanumeric)
   - Hashes each token to a bucket (0-383)
   - Weights by term frequency (1 + log(count))
   - L2 normalizes the vector
   - **No API calls, no quota limits, deterministic**
3. **Indexing** ([src/retrieval.py](src/retrieval.py)): Vectors + text + metadata stored in Chroma (persistent SQLite DB in `vector_store/`)

## Build Index

```powershell
& ".venv/Scripts/python.exe" -m src.main index "data/BU_HR_Manual_.pdf"
```

Output: `vector_store/` directory created with embedded chunks (234 chunks from your PDF).

Optional tuning:

```powershell
& ".venv/Scripts/python.exe" -m src.main index "data/BU_HR_Manual_.pdf" --chunk_size 900 --overlap 150
```

## Test Retrieval

Run the built-in retrieval test:

```powershell
& ".venv/Scripts/python.exe" test_retrieval.py
```

This runs a hardcoded query ("HR policy employee benefits") and shows top-3 chunks with similarity scores.

**Or test manually with any query:**

```powershell
& ".venv/Scripts/python.exe" -m src.main ask "What are leave policies?" --top_k 5
```

Shows:
- Grounded answer (extractive sentences from top chunks)
- Retrieved contexts with page numbers

## How Retrieval Works

Retrieval is handled by [src/retrieval.py](src/retrieval.py):

1. **Query Embedding**: Your question is converted to a 384-dim vector using the same embedding function as indexing (deterministic hash-based)
2. **Similarity Search**: Chroma compares your query vector against all 234 indexed chunk vectors using cosine similarity
3. **Top-K Selection**: Returns the top-k most similar chunks (default k=5)
4. **Metadata Return**: Each result includes:
   - `chunk_text`: The actual text from the PDF
   - `similarity_score`: Cosine similarity (0 to 1, higher is better)
   - `metadata`: Source file, page number

### Retrieval API

If you want to call retrieval directly in Python code:

```python
from src import embedding, retrieval

# 1. Embed your question
query = "What are the leave policies?"
query_embedding = embedding.get_embeddings([query])[0]

# 2. Retrieve top-k similar chunks
results = retrieval.retrieve_similar_chunks(
    query_text=query,
    query_embedding=query_embedding,
    collection_name="documents",
    persist_dir="vector_store",
    top_k=5,
)

# 3. Results is a list of tuples: (chunk_text, similarity, metadata)
for chunk_text, similarity, meta in results:
    print(f"Score: {similarity:.4f} | Page {meta['page']}")
    print(chunk_text[:200])
```

### Why Cosine Similarity?

- Vectors are L2-normalized, so cosine similarity = dot product
- Fast, interpretable (0=orthogonal, 1=identical)
- Works well for short to medium text chunks



## Ask Questions

```powershell
& ".venv/Scripts/python.exe" -m src.main ask "What are the annual holiday policies?" --top_k 5
```

## Basic Evaluation

```powershell
& ".venv/Scripts/python.exe" eval_basic.py
```

Runs 3 sample questions and reports pass/fail.

## Notes

- Embedded data lives in `vector_store/` (Chroma SQLite + index files)
- Current answer generation is extractive (grounded from retrieved text).
- Next improvement: add reranking + LLM synthesis while preserving citations.
- Backend auth supports long passwords without manual truncation.
