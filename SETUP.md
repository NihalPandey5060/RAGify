# RAG Project - Complete Setup Guide

This document explains how to set up and run the complete RAG system with both the core RAG pipeline and the FastAPI backend.

## Project Structure

```
rag_project/
├── README.md                    # Main project documentation
├── requirements.txt             # Core RAG dependencies
├── data/                        # Sample documents
│   └── BU_HR_Manual_.pdf
├── src/                         # Core RAG modules
│   ├── main.py                  # CLI entry point
│   ├── ingestion.py             # PDF processing
│   ├── embedding.py             # Local embeddings
│   ├── retrieval.py             # Chroma vector database
│   ├── generation.py            # Answer synthesis
│   └── __init__.py
├── vector_store/                # Vector database (auto-created)
│   └── [Chroma SQLite files]
├── backend/                     # FastAPI server
│   ├── README.md                # Backend documentation
│   ├── requirements.txt         # FastAPI dependencies
│   ├── .env.example             # Environment template
│   ├── test_api.py              # API test script
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # Pydantic schemas
│   │   ├── dependencies.py      # Auth dependency
│   │   ├── services/            # Business logic
│   │   ├── routes/              # API endpoints
│   │   └── utils/               # Helpers
│   └── chroma_db/               # Backend vector database
└── .gitignore
```

## Setup Instructions

### Step 1: Set Up Core RAG System

Navigate to the root directory:

```bash
cd rag_project
```

Create and activate virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

Install core dependencies:

```bash
pip install -r requirements.txt
```

### Step 2: Build the Vector Index

Index a PDF document (using the CLI):

```bash
python -m src.main index "data/BU_HR_Manual_.pdf"
```

Expected output:
```
[1/3] Ingesting... ✓ Created 234 chunks
[2/3] Embedding 234 chunks... ✓ Generated embeddings (dim=384)
[3/3] Indexing into Chroma... Indexed 234 chunks...
✓ Index saved to vector_store/
✅ RAG index built successfully!
```

### Step 3: Test Core RAG System

Ask a question via CLI:

```bash
python -m src.main ask "What is the annual leave policy?" --top_k 3
```

Run the test suite:

```bash
python test_retrieval.py
python eval_basic.py
```

### Step 4: Set Up FastAPI Backend

Navigate to backend directory:

```bash
cd backend
```

Create and activate virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

Install FastAPI dependencies:

```bash
pip install -r requirements.txt
```

Configure environment:

```bash
cp .env.example .env
# Edit .env and set a SECRET_KEY
# Example: openssl rand -hex 32 on macOS/Linux
# Or: python -c "import secrets; print(secrets.token_hex(32))" on Windows
```

### Step 5: Run FastAPI Server

```bash
python -m uvicorn app.main:app --reload
```

Server running on:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Step 6: Test the API

In a new terminal (from `backend/` directory):

```bash
python test_api.py
```

This runs through all endpoints:
1. Health check
2. User signup
3. Get current user
4. Document upload
5. Query endpoint
6. Streaming query endpoint

## Usage Examples

### Core RAG (CLI)

```bash
# From root directory, with .venv activated

# Build index
python -m src.main index "data/BU_HR_Manual_.pdf"

# Ask questions
python -m src.main ask "What does manual say about exit interview?"
python -m src.main ask "Employee benefits?" --top_k 5
```

### FastAPI Backend

From `backend/` directory with `venv` activated:

```bash
# Start server
python -m uvicorn app.main:app --reload

# Test endpoints (in another terminal)
curl -X GET http://localhost:8000/health

# Signup
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Upload document
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@../data/BU_HR_Manual_.pdf"

# Query
curl -X POST http://localhost:8000/query/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is annual leave?", "top_k": 5}'

# Stream
curl -X POST http://localhost:8000/query/ask-stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Exit process", "top_k": 5}'
```

## Core RAG System Details

### Pipeline Overview

1. **Ingestion**: Extract text from PDF using `pypdf`
2. **Chunking**: Split text with overlap (1000 chars, 200 overlap)
3. **Embedding**: Convert chunks to 384-dim vectors (local hash-based)
4. **Indexing**: Store in Chroma with cosine similarity
5. **Retrieval**: Find top-k similar chunks for query
6. **Generation**: Synthesize extractive answer from chunks

### Key Components

| Module | Purpose | Inputs | Outputs |
|--------|---------|--------|---------|
| `ingestion.py` | Extract PDF text | `pdf_path` | List of chunks with metadata |
| `embedding.py` | Generate vectors | Text list | 384-dim embeddings |
| `retrieval.py` | Index & retrieve | Chunks | Top-k similar chunks |
| `generation.py` | Synthesize answer | Query + chunks | Grounded answer with citations |

### Embedding Strategy

- **Type**: Local deterministic hash-based
- **Dimension**: 384 (configurable via `RAG_EMBED_DIM`)
- **Algorithm**: 
  1. Tokenize text → Hash tokens to buckets (0-383)
  2. Weight by term frequency (1 + log(count))
  3. L2 normalize vector
- **Why**: No API calls, no quotas, deterministic, fast

### Vector Database

- **System**: Chromadb with SQLite persistence
- **Location**: `./vector_store/` (root) or `./chroma_db/` (backend)
- **Similarity Metric**: Cosine distance
- **Features**: Automatic persistence, idempotent indexing

## FastAPI Backend Details

### Architecture

- **Framework**: FastAPI with Uvicorn
- **Authentication**: JWT tokens with bcrypt password hashing
- **Database**: Chromadb (shared with core RAG)
- **Caching**: In-memory dictionary with TTL
- **Streaming**: NDJSON format for real-time responses

### API Features

- **Auth**: Signup, login, get current user
- **Documents**: Upload PDF/text, auto-index
- **Queries**: Standard and streaming endpoints
- **Protection**: All RAG endpoints require JWT token
- **Caching**: Automatic query result caching (60 min TTL)

### Dependency Structure

```
User Auth Request
    ↓
HTTPBearer (extract token)
    ↓
get_current_user (validate JWT)
    ↓
Route handler (receives user_id, email)
    ↓
RAG service (retrieve/generate)
    ↓
Response
```

## Configuration

### Root `.env`
```env
# Optional if using API keys in future
# OPENAI_API_KEY=sk-...
```

### Backend `.env`
```env
SECRET_KEY=generated-random-key
CHROMA_DB_DIR=./chroma_db
RAG_EMBED_DIM=384
```

## Troubleshooting

### Core RAG Issues

| Issue | Solution |
|-------|----------|
| "No chunks extracted from PDF" | Ensure PDF is text-based (not scanned image) |
| "Vector store locked" | Delete `vector_store/` and re-index |
| "Index not found" | Run `python -m src.main index "path/to/pdf"` first |

### FastAPI Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure server is running: `uvicorn app.main:app --reload` |
| "Invalid token" | Login again, get new token: `POST /auth/login` |
| "Database locked" | Restart server, clear `chroma_db/` if needed |
| "No relevant documents" | Upload document first: `POST /documents/upload` |

### General Setup Issues

| Issue | Solution |
|-------|----------|
| "Module not found" | Ensure you're in correct directory with venv activated |
| "pip install fails" | Try `pip install --upgrade pip` first |
| "Port 8000 in use" | Change port: `--port 8001` |

## Development Workflow

### Local Testing

```bash
# Terminal 1: Core RAG development
cd rag_project
.venv\Scripts\activate
python -m src.main ask "test query"

# Terminal 2: Backend development
cd rag_project/backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload

# Terminal 3: API testing
cd rag_project/backend
python test_api.py
```

### Deployment

For production deployment, refer to:
- **Backend README**: `backend/README.md` (Docker, Gunicorn, Render)
- **Core RAG**: Use as library in production backend

## Next Steps

- [ ] Add LLM-based answer generation (OpenAI integration)
- [ ] Support multi-document indexing
- [ ] Add user feedback mechanism
- [ ] Deploy to cloud (Render, Railway, Azure)
- [ ] Add vector database monitoring
- [ ] Implement rate limiting
- [ ] Add batch processing endpoint
- [ ] Create web UI for document management

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review API docs: http://localhost:8000/docs
3. Check individual README files:
   - `README.md` (core RAG)
   - `backend/README.md` (FastAPI backend)

---

**Version**: 1.0.0  
**Last Updated**: January 2024
