"""
Pydantic models for API request/response schemas
"""

from .resume import ResumeBase, ResumeCreate, ResumeResponse, ParsedResumeResponse
from .scoring import ScoreRequest, ScoreResponse, SuggestionResponse
from .job_description import JobDescriptionCreate, JobDescriptionResponse

__all__ = [
    "ResumeBase",
    "ResumeCreate", 
    "ResumeResponse",
    "ParsedResumeResponse",
    "ScoreRequest",
    "ScoreResponse",
    "SuggestionResponse",
    "JobDescriptionCreate",
    "JobDescriptionResponse"
]