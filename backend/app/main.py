from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, documents, query
from app.db import init_db


init_db()


# Initialize FastAPI app
app = FastAPI(
    title="RAG API",
    description="Production RAG system with authentication",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Routes ==============

# Auth routes (public)
app.include_router(auth.router)

# Protected routes
app.include_router(documents.router)
app.include_router(query.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """API root."""
    return {
        "title": "RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
