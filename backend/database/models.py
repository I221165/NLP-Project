"""
Database models for multi-user system
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pdfs = relationship("PDF", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    weaknesses = relationship("Weakness", back_populates="user", cascade="all, delete-orphan")


class PDF(Base):
    """PDF document model"""
    __tablename__ = "pdfs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_id = Column(String(255), unique=True, index=True, nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    total_chunks = Column(Integer, default=0)
    file_size = Column(Integer)  # in bytes
    
    # Relationships
    user = relationship("User", back_populates="pdfs")
    chats = relationship("Chat", back_populates="pdf", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="pdf", cascade="all, delete-orphan")


class Chat(Base):
    """Chat history model"""
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=False)
    messages = Column(JSON, default=list)  # [{role: "user/assistant", content: "...", timestamp: "..."}]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chats")
    pdf = relationship("PDF", back_populates="chats")


class Quiz(Base):
    """Quiz model"""
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=False)
    topic = Column(String(500))
    questions = Column(JSON)  # Quiz questions array
    user_answers = Column(JSON)  # User's answers
    score = Column(Float)  # Percentage score
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="quizzes")
    pdf = relationship("PDF", back_populates="quizzes")


class Weakness(Base):
    """User weakness tracking"""
    __tablename__ = "weaknesses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    concept = Column(String(500), nullable=False)  # Keyword/concept
    frequency = Column(Integer, default=1)  # How many times incorrect
    last_incorrect_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="weaknesses")
