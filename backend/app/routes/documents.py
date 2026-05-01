from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
import os
import tempfile
from app.models import DocumentUploadResponse
from app.services import rag as rag_service
from app.dependencies import get_current_user


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a document (PDF or text) and index it."""
    user_id = current_user["user_id"]
    
    try:
        contents = await file.read()
        
        # Determine file type and extract text
        if file.filename.endswith(".pdf"):
            # Save PDF temporarily in a cross-platform location
            suffix = os.path.splitext(file.filename)[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(contents)
                temp_path = tmp.name
            try:
                text = rag_service.extract_text_from_pdf(temp_path)
            finally:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
        else:
            # Assume text file
            text = contents.decode("utf-8")
        
        # Chunk the text
        chunks = rag_service.chunk_text(text, chunk_size=1000, overlap=200)
        
        # Store chunks in Chroma
        chunk_count = rag_service.store_document_chunks(chunks, user_id)
        
        return DocumentUploadResponse(
            message=f"Document '{file.filename}' uploaded successfully",
            chunk_count=chunk_count,
            status="indexed"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process document: {str(e)}"
        )
