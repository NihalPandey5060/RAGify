# RAG API Backend

A production-ready FastAPI backend for the RAG (Retrieval-Augmented Generation) system with JWT authentication, document upload, streaming queries, and query caching.

## Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── models.py               # Pydantic schemas
│   ├── services/
│   │   ├── auth.py             # JWT and password hashing
│   │   ├── rag.py              # Document processing and retrieval
│   │   ├── cache.py            # Query caching
│   │   └── __init__.py
│   ├── routes/
│   │   ├── auth.py             # POST /signup, /login, GET /me
│   │   ├── documents.py        # POST /upload
│   │   ├── query.py            # POST /ask, /ask-stream
│   │   └── __init__.py
│   └── utils/
│       ├── answer.py           # Answer synthesis
│       └── __init__.py
├── requirements.txt
├── .env.example
└── README.md (this file)
```

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and change SECRET_KEY to a random string
```

### 4. Run Server

```bash
python -m uvicorn app.main:app --reload
```

Server runs on `http://localhost:8000`

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication (Public)

#### 1. Sign Up
```bash
POST /auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-123",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

#### 2. Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** Same as signup

#### 3. Get Current User
```bash
GET /auth/me
Authorization: Bearer <your-token>
```

**Response:**
```json
{
  "id": "uuid-123",
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00"
}
```

---

### Document Upload (Protected)

#### Upload Document
```bash
POST /documents/upload
Authorization: Bearer <your-token>
Content-Type: multipart/form-data

[file: @path/to/document.pdf]
```

**Response:**
```json
{
  "message": "Document 'BU_HR_Manual.pdf' uploaded successfully",
  "chunk_count": 234,
  "status": "indexed"
}
```

Supported formats: PDF, TXT

---

### Query (Protected)

#### Ask Question (Non-Streaming)
```bash
POST /query/ask
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "query": "What are the annual holidays?",
  "top_k": 5
}
```

**Response:**
```json
{
  "question": "What are the annual holidays?",
  "answer": "- Employees are entitled to 20 days of leave per year (page=5)\n- Leave can be taken in blocks or individual days (page=5)\n- Advance notice of 2 weeks is required for leave requests (page=6)",
  "retrieved_chunks": [
    {
      "text": "Employees are entitled to 20 days of leave per year...",
      "similarity": 0.85,
      "metadata": {"page": 5, "chunk_idx": 0}
    }
  ],
  "cache_hit": false
}
```

#### Ask Question (Streaming)
```bash
POST /query/ask-stream
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "query": "What is the exit process?",
  "top_k": 5
}
```

**Response (NDJSON - newline-delimited JSON):**
```
{"type": "retrieval_complete", "chunk_count": 3}
{"type": "answer_chunk", "content": "- "}
{"type": "answer_chunk", "content": "Employees "}
{"type": "answer_chunk", "content": "must "}
...
{"type": "complete"}
```

---

## Example Usage

### Using cURL

#### 1. Sign Up
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "secure123"
  }'
```

#### 2. Upload Document
```bash
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@BU_HR_Manual.pdf"
```

#### 3. Ask Question
```bash
curl -X POST http://localhost:8000/query/ask \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the exit interview process?",
    "top_k": 5
  }'
```

#### 4. Stream Answer
```bash
curl -X POST http://localhost:8000/query/ask-stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about employee benefits",
    "top_k": 5
  }' | jq -R 'fromjson'
```

### Using Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Sign up
signup_response = requests.post(
    f"{BASE_URL}/auth/signup",
    json={"email": "user@example.com", "password": "password123"}
)
token = signup_response.json()["access_token"]

# Upload document
headers = {"Authorization": f"Bearer {token}"}
with open("BU_HR_Manual.pdf", "rb") as f:
    files = {"file": f}
    upload_response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files
    )
    print(upload_response.json())

# Ask question
query_response = requests.post(
    f"{BASE_URL}/query/ask",
    headers=headers,
    json={"query": "What is the annual leave policy?", "top_k": 5}
)
result = query_response.json()
print(f"Answer: {result['answer']}")
print(f"Cache hit: {result['cache_hit']}")

# Stream answer
stream_response = requests.post(
    f"{BASE_URL}/query/ask-stream",
    headers=headers,
    json={"query": "Exit process", "top_k": 5},
    stream=True
)
for line in stream_response.iter_lines():
    if line:
        print(json.loads(line))
```

## Key Features

### 1. Authentication
- **JWT-based** with HTTPBearer scheme
- **Signup/Login** endpoints for user registration
- **Token expiration** (60 minutes default)
- **Password hashing** with PBKDF2-HMAC SHA-256 for long-password safety
- **Long passwords** are supported without manual truncation

### 2. Document Management
- **Single document** per user
- Supports **PDF** and **text** files
- **Automatic chunking** with overlap (1000 chars, 200 overlap)
- **Persistent storage** in Chroma (local SQLite DB)

### 3. Query Processing
- **Local embeddings** (384-dim hash-based, no API calls)
- **Cosine similarity** retrieval
- **Extractive answer** synthesis with citations
- **Streaming support** for real-time responses
- **Query caching** (60 minutes default)

### 4. Production Ready
- **CORS** enabled for cross-origin requests
- **Error handling** with HTTP exceptions
- **Health check** endpoint
- **Swagger/OpenAPI** documentation
- **NDJSON streaming** for efficient data transfer

## Configuration

Edit `.env` to customize:

```env
HOST=0.0.0.0              # Server bind address
PORT=8000                 # Server port
SECRET_KEY=...            # JWT signing key (REQUIRED)
RAG_EMBED_DIM=384         # Embedding vector dimension
CHROMA_DB_DIR=./chroma_db # Vector store location
```

## Deployment

### Local Development
```bash
python -m uvicorn app.main:app --reload
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### Render/Railway
```bash
# Copy .env.example to .env and set variables in dashboard
# Deploy git repository directly
```

## Troubleshooting

**"No relevant documents found"**
- Upload a document first using POST /documents/upload
- Ensure the query is related to document content

**"Invalid or expired token"**
- Login again to get a new token
- Tokens expire after 60 minutes

**"Database locked"**
- Restart the server
- Clear ./chroma_db and re-upload documents

**Slow queries**
- Increase `top_k` to retrieve more context
- Use streaming endpoint for better UX

## Future Enhancements

- [ ] Multi-document support per user
- [ ] LLM-based answer generation (OpenAI)
- [ ] Advanced caching with Redis
- [ ] Batch query processing
- [ ] Document metadata extraction
- [ ] User feedback on answer quality
- [ ] Admin dashboard

## License

MIT
