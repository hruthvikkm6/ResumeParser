"""
Pydantic models for resume-related operations
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    gpa: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    details: Optional[List[str]] = []


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    details: Optional[List[str]] = []


class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    url: Optional[str] = None


class Skills(BaseModel):
    technical: Optional[List[str]] = []
    soft: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    certifications: Optional[List[str]] = []


class ResumeBase(BaseModel):
    """Base resume model"""
    filename: str
    
    
class ResumeCreate(ResumeBase):
    """Model for creating a new resume"""
    pass


class ParsedResumeResponse(BaseModel):
    """Response model for parsed resume data"""
    id: str
    filename: str
    
    # Extracted information
    contact_info: ContactInfo
    skills: Skills
    education: List[Education]
    experience: List[Experience]
    projects: Optional[List[Project]] = []
    
    # Raw data
    raw_text: str
    
    # Metadata
    created_at: datetime
    
    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    """Simple resume response model"""
    id: str
    filename: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ResumeList(BaseModel):
    """Model for listing multiple resumes"""
    resumes: List[ResumeResponse]
    total: int
    page: int = 1
    page_size: int = 10