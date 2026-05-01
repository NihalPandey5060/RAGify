from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
import json
import asyncio
from app.models import QueryRequest, QueryResponse, RetrievedChunk
from app.services import rag as rag_service
from app.services import cache as cache_service
from app.utils import answer as answer_utils
from app.dependencies import get_current_user


router = APIRouter(prefix="/query", tags=["query"])


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Query the RAG system (non-streaming, with caching)."""
    
    user_id = current_user["user_id"]
    query = request.query
    top_k = request.top_k
    
    # Check cache
    cache_key = cache_service.get_cache_key(query, user_id)
    cached_result = cache_service.get_cache(cache_key)
    
    if cached_result:
        cached_result["cache_hit"] = True
        return cached_result
    
    # Retrieve chunks
    retrieved = rag_service.retrieve_chunks(query, user_id, top_k=top_k)
    
    if not retrieved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relevant documents found"
        )
    
    # Synthesize answer
    answer_text = answer_utils.synthesize_answer(query, retrieved)
    
    # Format response
    retrieved_chunks = [
        RetrievedChunk(
            text=chunk_text,
            similarity=similarity,
            metadata=metadata
        )
        for chunk_text, similarity, metadata in retrieved
    ]
    
    response = QueryResponse(
        question=query,
        answer=answer_text,
        retrieved_chunks=retrieved_chunks,
        cache_hit=False
    )
    
    # Cache the result
    cache_service.set_cache(cache_key, response.dict())
    
    return response


async def _generate_streaming_answer(query: str, user_id: str, top_k: int):
    """Generate answer chunks for streaming."""
    try:
        # Retrieve chunks
        retrieved = rag_service.retrieve_chunks(query, user_id, top_k=top_k)
        
        if not retrieved:
            yield json.dumps({"error": "No relevant documents found"}) + "\n"
            return
        
        # Stream retrieval info
        yield json.dumps({
            "type": "retrieval_complete",
            "chunk_count": len(retrieved)
        }) + "\n"
        
        # Generate answer
        answer_text = answer_utils.synthesize_answer(query, retrieved)
        
        # Stream answer word-by-word
        words = answer_text.split()
        for word in words:
            await asyncio.sleep(0.05)  # Simulate streaming delay
            yield json.dumps({
                "type": "answer_chunk",
                "content": word + " "
            }) + "\n"
        
        yield json.dumps({"type": "complete"}) + "\n"
    
    except Exception as e:
        yield json.dumps({"type": "error", "message": str(e)}) + "\n"


@router.post("/ask-stream")
async def ask_question_stream(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Query the RAG system with streaming response."""
    
    user_id = current_user["user_id"]
    
    return StreamingResponse(
        _generate_streaming_answer(request.query, user_id, request.top_k),
        media_type="application/x-ndjson"
    )
