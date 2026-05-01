# FastAPI Backend - Quick Start

## 60-Second Setup

### 1. Move to backend directory
```bash
cd backend
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env and change SECRET_KEY to something random
# You can use: python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Start the server
```bash
python -m uvicorn app.main:app --reload
```

**Server is running at**: http://localhost:8000
**API Docs**: http://localhost:8000/docs

---

## Quick API Test (5 minutes)

### In a new terminal from backend directory:

```bash
python test_api.py
```

This will:
1. ✅ Check server is running
2. ✅ Create a test user (signup)
3. ✅ Verify user retrieval
4. ✅ Upload a document (PDF)
5. ✅ Run a query
6. ✅ Test streaming endpoint

---

## Manual Testing with cURL

### 1. Signup
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "password123"
  }'
```

Copy the `access_token` from the response.

### 2. Upload Document
```bash
# Make sure ../data/BU_HR_Manual_.pdf exists
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@../data/BU_HR_Manual_.pdf"
```

### 3. Ask a Question
```bash
curl -X POST http://localhost:8000/query/ask \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the annual leave policy?",
    "top_k": 5
  }'
```

### 4. Stream a Response
```bash
curl -X POST http://localhost:8000/query/ask-stream \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"query": "Exit interview process", "top_k": 5}'
```

---

## Using Swagger UI

Open http://localhost:8000/docs in your browser

1. Click "Try it out" on any endpoint
2. For protected endpoints, click the lock icon at the top right
3. Paste your JWT token: `YOUR_TOKEN_HERE`
4. Execute requests directly from the browser

---

## File Structure

```
backend/
├── app/
│   ├── main.py              ← FastAPI app
│   ├── models.py            ← Request/response schemas
│   ├── dependencies.py      ← Auth dependency
│   ├── services/            ← Business logic
│   ├── routes/              ← API endpoints
│   └── utils/               ← Helpers
├── test_api.py              ← Full test suite
├── requirements.txt         ← Dependencies
├── .env.example             ← Config template
├── .env                     ← Your config (create from .env.example)
└── README.md                ← Full documentation
```

---

## Key Features

🔐 **JWT Authentication**
- Signup, login, get current user
- 60-minute token expiration
- PBKDF2-HMAC SHA-256 password hashing
- Long passwords work without truncation

📄 **Document Management**
- Upload PDF or text files
- Automatic chunking and indexing
- Stores in local vector database

🔍 **Query Processing**
- Retrieve relevant chunks
- Streaming responses
- Query result caching

---

## Troubleshooting

**"Connection refused"**
- Is the server running? `python -m uvicorn app.main:app --reload`

**"Invalid token"**
- Login again: `POST /auth/login`

**"No relevant documents found"**
- Upload a document first: `POST /documents/upload`

**"Database locked"**
- Restart the server
- Delete `chroma_db/` folder if needed

---

## Environment Variables (in .env)

```env
SECRET_KEY=your-random-secret-key-here
HOST=0.0.0.0
PORT=8000
CHROMA_DB_DIR=./chroma_db
RAG_EMBED_DIM=384
```

---

## Next Steps

1. ✅ **Start Server**: `python -m uvicorn app.main:app --reload`
2. ✅ **Test API**: `python test_api.py`
3. ✅ **Explore Docs**: http://localhost:8000/docs
4. 📚 **Read Full Docs**: See `README.md` for detailed API reference
5. 🚀 **Deploy**: See `README.md` for Docker, Gunicorn, Render setup

---

**Need help?** See `README.md` for complete documentation.
