"""
Database configuration and models
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Float, JSON
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class Resume(Base):
    __tablename__ = "resumes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Extracted fields
    name: Mapped[Optional[str]] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # JSON fields for complex data
    skills: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    experience: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    education: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Raw data
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    parsed_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    
    # Extracted features
    required_skills: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    keywords: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResumeScore(Base):
    __tablename__ = "resume_scores"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id: Mapped[str] = mapped_column(String(36))
    job_description_id: Mapped[Optional[str]] = mapped_column(String(36))
    
    # Scores
    overall_score: Mapped[float] = mapped_column(Float)
    skills_score: Mapped[Optional[float]] = mapped_column(Float)
    experience_score: Mapped[Optional[float]] = mapped_column(Float)
    education_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Analysis results
    matched_keywords: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    missing_keywords: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    suggestions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Raw job description text for scoring
    job_description_text: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Dependency to get database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Initialize database
async def init_db():
    """Create database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)