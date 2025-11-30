"""
Pydantic models for scoring and ATS-related operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ScoreRequest(BaseModel):
    """Request model for scoring a resume against a job description"""
    resume_id: str = Field(..., description="ID of the parsed resume")
    job_description: str = Field(..., description="Job description text", min_length=50)
    job_title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    
    # Optional scoring parameters
    use_sbert: bool = Field(False, description="Use SBERT embeddings for enhanced scoring")
    score_weights: Optional[Dict[str, float]] = Field(
        None, 
        description="Custom weights for scoring sections",
        example={"skills": 0.4, "experience": 0.35, "education": 0.25}
    )


class SectionScore(BaseModel):
    """Score for a specific resume section"""
    section: str
    score: float = Field(..., ge=0.0, le=1.0)
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []
    weight: float = Field(..., ge=0.0, le=1.0)


class ScoreResponse(BaseModel):
    """Response model for resume scoring"""
    score_id: str
    resume_id: str
    
    # Overall scoring
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall ATS compatibility score")
    
    # Section-wise scores
    section_scores: List[SectionScore] = []
    
    # Keyword analysis
    total_matched_keywords: List[str] = []
    total_missing_keywords: List[str] = []
    keyword_density: float = Field(..., ge=0.0, le=1.0)
    
    # Metadata
    job_title: Optional[str] = None
    company: Optional[str] = None
    scoring_method: str = Field(default="tfidf", description="Method used for scoring")
    created_at: datetime
    
    class Config:
        from_attributes = True


class Suggestion(BaseModel):
    """Individual improvement suggestion"""
    type: str = Field(..., description="Type of suggestion (skills, experience, format, etc.)")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed suggestion")
    keywords_to_add: Optional[List[str]] = Field([], description="Specific keywords to include")
    
    
class SuggestionResponse(BaseModel):
    """Response model for resume improvement suggestions"""
    resume_id: str
    score_id: Optional[str] = None
    
    # Categorized suggestions
    suggestions: List[Suggestion] = []
    
    # Summary statistics
    total_suggestions: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    
    # Quick wins
    missing_critical_keywords: List[str] = []
    formatting_issues: List[str] = []
    
    created_at: datetime


class ScoringSummary(BaseModel):
    """Summary statistics for dashboard"""
    total_resumes: int
    average_score: float
    score_distribution: Dict[str, int]  # score ranges and counts
    common_missing_skills: List[Dict[str, Any]]  # skill and frequency
    top_performing_resumes: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]