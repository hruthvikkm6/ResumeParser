"""
Pydantic models for job description operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class JobDescriptionCreate(BaseModel):
    """Model for creating a new job description"""
    title: str = Field(..., min_length=3, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    description: str = Field(..., min_length=100, description="Job description text")


class JobDescriptionResponse(BaseModel):
    """Response model for job description"""
    id: str
    title: str
    company: Optional[str]
    description: str
    
    # Extracted features
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    keywords: Optional[List[str]] = []
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobDescriptionAnalysis(BaseModel):
    """Analysis of job description for key requirements"""
    jd_id: str
    
    # Skill categories
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    certifications: List[str] = []
    tools_and_technologies: List[str] = []
    
    # Experience requirements
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    seniority_level: Optional[str] = None  # entry, mid, senior, lead
    
    # Education requirements
    required_degree: Optional[str] = None
    preferred_degree: Optional[str] = None
    field_of_study: Optional[List[str]] = []
    
    # Key phrases and requirements
    must_have_keywords: List[str] = []
    nice_to_have_keywords: List[str] = []
    
    # Industry and domain
    industry: Optional[str] = None
    domain: Optional[str] = None
    
    # Location and work arrangements
    location: Optional[str] = None
    remote_work: Optional[bool] = None
    travel_required: Optional[bool] = None