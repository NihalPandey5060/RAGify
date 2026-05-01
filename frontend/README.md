# Frontend

A minimal static frontend for the FastAPI RAG backend.

## What it does

- Signup and login with JWT storage in `localStorage`
- Upload one document to the backend
- Ask questions with normal or streaming responses
- Display chat messages in a simple interface

## Backend endpoints used

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /documents/upload`
- `POST /query/ask`
- `POST /query/ask-stream`

## How to run

This is a static app, so serve it with any local web server.

### Option 1: Python

From the project root:

```powershell
cd frontend
python -m http.server 5173
```

Then open:

```text
http://localhost:5173
```

### Option 2: VS Code Live Server

Open `frontend/index.html` and use Live Server.

## Notes

- The backend must be running at `http://localhost:8000`.
- Protected routes require `Authorization: Bearer <token>`.
- Streaming uses `POST /query/ask-stream` and reads NDJSON events progressively.
- If you want to change the backend URL, edit `API_BASE` in `app.js`.
