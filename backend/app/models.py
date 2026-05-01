from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ============== Auth Models ==============

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============== Document Models ==============

class DocumentUploadResponse(BaseModel):
    message: str
    chunk_count: int
    status: str


# ============== Query Models ==============

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class RetrievedChunk(BaseModel):
    text: str
    similarity: float
    metadata: dict


class QueryResponse(BaseModel):
    question: str
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    cache_hit: bool


# ============== Error Models ==============

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
