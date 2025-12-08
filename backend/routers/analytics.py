"""
Analytics router - Weakness tracking and progress
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from database.connection import get_db
from database.models import User, Weakness, Quiz as QuizModel
from auth.middleware import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# Pydantic models
class WeaknessResponse(BaseModel):
    concept: str
    frequency: int
    last_incorrect: str


class ProgressResponse(BaseModel):
    total_quizzes: int
    average_score: float
    total_pdfs: int
    weak_concepts_count: int


@router.get("/weaknesses", response_model=List[WeaknessResponse])
async def get_weaknesses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's weak concepts sorted by frequency"""
    weaknesses = db.query(Weakness).filter(
        Weakness.user_id == current_user.id
    ).order_by(Weakness.frequency.desc()).limit(10).all()
    
    return [
        {
            "concept": w.concept,
            "frequency": w.frequency,
            "last_incorrect": w.last_incorrect_at.isoformat()
        }
        for w in weaknesses
    ]


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall progress statistics"""
    # Total quizzes
    total_quizzes = db.query(QuizModel).filter(
        QuizModel.user_id == current_user.id
    ).count()
    
    # Average score
    avg_score = db.query(func.avg(QuizModel.score)).filter(
        QuizModel.user_id == current_user.id
    ).scalar() or 0.0
    
    # Total PDFs
    from database.models import PDF as PDFModel
    total_pdfs = db.query(PDFModel).filter(
        PDFModel.user_id == current_user.id
    ).count()
    
    # Weak concepts count
    weak_concepts_count = db.query(Weakness).filter(
        Weakness.user_id == current_user.id
    ).count()
    
    return {
        "total_quizzes": total_quizzes,
        "average_score": float(avg_score),
        "total_pdfs": total_pdfs,
        "weak_concepts_count": weak_concepts_count
    }
