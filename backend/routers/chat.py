"""
Chat router - Q&A system with RAG retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
from logging_config import get_logger

from database.connection import get_db
from database.models import User, PDF as PDFModel, Chat as ChatModel
from auth.middleware import get_current_user
from services.rag_service import rag_service
from services.groq_client import groq_client

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger(__name__)


# Pydantic models
class ChatRequest(BaseModel):
    pdf_id: str
    question: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    chat_id: str


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question about a PDF using RAG"""
    logger.info(f"Chat question received", extra={
        "user_id": str(current_user.id),
        "pdf_id": request.pdf_id
    })
    
    # Verify PDF ownership
    pdf = db.query(PDFModel).filter(
        PDFModel.id == request.pdf_id,
        PDFModel.user_id == current_user.id
    ).first()
    
    if not pdf:
        logger.warning(f"PDF not found", extra={"pdf_id": request.pdf_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found"
        )
    
    # Retrieve relevant chunks using RAG (increased context for better answers)
    retrieval_result = await rag_service.query_document(
        user_id=str(current_user.id),
        file_id=pdf.file_id,
        query=request.question,
        top_k=10  # Increased from 5 for more comprehensive answers
    )
    
    chunks = retrieval_result.get("chunks", [])
    chunk_texts = [chunk["text"] for chunk in chunks]
    
    # Generate answer using Groq
    groq_result = await groq_client.answer_question(
        question=request.question,
        context_chunks=chunk_texts
    )
    
    answer = groq_result.get("answer", "Sorry, I couldn't generate an answer.")
    
    logger.info("Answer generated successfully", extra={
        "answer_length": len(answer),
        "num_sources": len(chunks)
    })
    
    # Get or create chat session
    chat = db.query(ChatModel).filter(
        ChatModel.user_id == current_user.id,
        ChatModel.pdf_id == pdf.id
    ).first()
    
    if not chat:
        chat = ChatModel(
            user_id=current_user.id,
            pdf_id=pdf.id,
            messages=[]
        )
        db.add(chat)
    
    # Append messages
    timestamp = datetime.utcnow().isoformat()
    chat.messages.append({
        "role": "user",
        "content": request.question,
        "timestamp": timestamp
    })
    chat.messages.append({
        "role": "assistant",
        "content": answer,
        "timestamp": timestamp
    })
    
    db.commit()
    db.refresh(chat)
    
    return {
        "answer": answer,
        "sources": chunks,
        "chat_id": str(chat.id)
    }


@router.get("/history/{pdf_id}", response_model=List[ChatMessage])
async def get_chat_history(
    pdf_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a PDF"""
    chat = db.query(ChatModel).filter(
        ChatModel.pdf_id == pdf_id,
        ChatModel.user_id == current_user.id
    ).first()
    
    if not chat:
        return []
    
    return chat.messages


@router.delete("/{chat_id}")
async def clear_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear chat history"""
    chat = db.query(ChatModel).filter(
        ChatModel.id == chat_id,
        ChatModel.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    db.delete(chat)
    db.commit()
    
    return {"message": "Chat history cleared"}
