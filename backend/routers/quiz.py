"""
Quiz router - Generate, submit, and track quizzes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database.connection import get_db
from database.models import User, PDF as PDFModel, Quiz as QuizModel, Weakness
from auth.middleware import get_current_user
from services.rag_service import rag_service
from services.groq_client import groq_client

router = APIRouter(prefix="/quiz", tags=["Quiz"])


# Pydantic models
class QuizGenerateRequest(BaseModel):
    pdf_id: str
    topic: str
    num_questions: int = 5
    difficulty: str = "medium"  # easy, medium, or hard


class QuizSubmitRequest(BaseModel):
    quiz_id: str
    user_answers: dict  # {question_id: selected_answer}


class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[dict]
    topic: str


class QuizResultResponse(BaseModel):
    quiz_id: str
    score: float
    correct_answers: int
    total_questions: int
    weak_concepts: List[str]


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate quiz from PDF using Groq"""
    # Verify PDF ownership
    pdf = db.query(PDFModel).filter(
        PDFModel.id == request.pdf_id,
        PDFModel.user_id == current_user.id
    ).first()
    
    if not pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found"
        )
    
    # Get relevant context
    context = await rag_service.get_document_context(
        user_id=str(current_user.id),
        file_id=pdf.file_id,
        topic=request.topic,
        top_k=10
    )
    
    # Generate quiz using Groq
    questions = await groq_client.generate_quiz(
        context=context,
        topic=request.topic,
        num_questions=request.num_questions,
        difficulty=request.difficulty
    )
    
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz questions"
        )
    
    # Save quiz to database
    quiz = QuizModel(
        user_id=current_user.id,
        pdf_id=pdf.id,
        topic=request.topic,
        questions=questions,
        user_answers={},
        total_questions=len(questions)
    )
    
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    return {
        "quiz_id": str(quiz.id),
        "questions": questions,
        "topic": request.topic
    }


@router.post("/submit", response_model=QuizResultResponse)
async def submit_quiz(
    request: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get results"""
    # Get quiz
    quiz = db.query(QuizModel).filter(
        QuizModel.id == request.quiz_id,
        QuizModel.user_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Grade quiz
    correct_count = 0
    incorrect_answers = []
    
    for question in quiz.questions:
        q_id = str(question["id"])
        correct_answer = question["correct_answer"]
        user_answer = request.user_answers.get(q_id, "")
        
        if user_answer.strip() == correct_answer.strip():
            correct_count += 1
        else:
            # Include concept tag for better weakness tracking
            incorrect_answers.append({
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "concept": question.get("concept", quiz.topic)
            })
    
    # Calculate score
    score = (correct_count / quiz.total_questions) * 100 if quiz.total_questions > 0 else 0
    
    # Update quiz record
    quiz.user_answers = request.user_answers
    quiz.score = score
    quiz.correct_answers = correct_count
    
    # Analyze weaknesses
    weak_concepts = []
    if incorrect_answers:
        # Use concept tags from questions first, then analyze with Groq
        concept_tags = [ans.get("concept", "") for ans in incorrect_answers if ans.get("concept")]
        groq_concepts = await groq_client.analyze_weaknesses(incorrect_answers)
        weak_concepts = list(set(concept_tags + groq_concepts))  # Combine and remove duplicates
        
        # Update weakness tracking
        for concept in weak_concepts:
            weakness = db.query(Weakness).filter(
                Weakness.user_id == current_user.id,
                Weakness.concept == concept
            ).first()
            
            if weakness:
                weakness.frequency += 1
            else:
                weakness = Weakness(
                    user_id=current_user.id,
                    concept=concept,
                    frequency=1
                )
                db.add(weakness)
    
    db.commit()
    
    return {
        "quiz_id": str(quiz.id),
        "score": score,
        "correct_answers": correct_count,
        "total_questions": quiz.total_questions,
        "weak_concepts": weak_concepts
    }


@router.get("/history")
async def get_quiz_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all quizzes for current user"""
    quizzes = db.query(QuizModel).filter(
        QuizModel.user_id == current_user.id
    ).order_by(QuizModel.completed_at.desc()).all()
    
    return [
        {
            "id": str(quiz.id),
            "topic": quiz.topic,
            "score": quiz.score,
            "completed_at": quiz.completed_at.isoformat()
        }
        for quiz in quizzes
    ]
