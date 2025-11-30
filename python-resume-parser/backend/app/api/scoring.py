"""
ATS Scoring API endpoints for resume analysis
"""

import uuid
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, Resume, ResumeScore, JobDescription
from app.models.scoring import ScoreRequest, ScoreResponse, SuggestionResponse, Suggestion
from app.models.job_description import JobDescriptionCreate, JobDescriptionResponse
from app.services.ats_scorer import ATSScorerService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize ATS scorer service
ats_scorer = ATSScorerService()


@router.post("/score_resume", response_model=ScoreResponse)
async def score_resume(
    request: ScoreRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Score a resume against a job description using ATS algorithms
    
    Args:
        request: ScoreRequest with resume ID and job description
        db: Database session
        
    Returns:
        ScoreResponse with detailed scoring results
    """
    
    # Get the parsed resume
    result = await db.execute(select(Resume).where(Resume.id == request.resume_id))
    db_resume = result.scalar_one_or_none()
    
    if not db_resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {request.resume_id} not found"
        )
    
    if not db_resume.parsed_data:
        raise HTTPException(
            status_code=400,
            detail="Resume has not been parsed yet"
        )
    
    try:
        logger.info(f"Scoring resume {request.resume_id} against job description")
        
        # Score the resume
        scoring_result = await ats_scorer.score_resume(
            parsed_resume=db_resume.parsed_data,
            job_description=request.job_description,
            use_sbert=request.use_sbert,
            custom_weights=request.score_weights
        )
        
        # Create score record
        score_id = str(uuid.uuid4())
        
        # Save score to database
        db_score = ResumeScore(
            id=score_id,
            resume_id=request.resume_id,
            overall_score=scoring_result['overall_score'],
            skills_score=scoring_result['section_scores'].get('skills', {}).get('score'),
            experience_score=scoring_result['section_scores'].get('experience', {}).get('score'),
            education_score=scoring_result['section_scores'].get('education', {}).get('score'),
            matched_keywords=scoring_result['matched_keywords'],
            missing_keywords=scoring_result['missing_keywords'],
            job_description_text=request.job_description
        )
        
        # Save job description if provided
        if request.job_title or request.company:
            jd_id = str(uuid.uuid4())
            db_jd = JobDescription(
                id=jd_id,
                title=request.job_title or "Untitled Position",
                company=request.company,
                description=request.job_description
            )
            db.add(db_jd)
            db_score.job_description_id = jd_id
        
        db.add(db_score)
        await db.commit()
        await db.refresh(db_score)
        
        logger.info(f"Successfully scored resume. Overall score: {scoring_result['overall_score']:.3f}")
        
        # Format section scores for response
        section_scores_list = []
        for section_name, section_data in scoring_result['section_scores'].items():
            section_scores_list.append({
                'section': section_name,
                'score': section_data['score'],
                'matched_keywords': section_data['matched_keywords'],
                'missing_keywords': section_data['missing_keywords'],
                'weight': section_data['weight']
            })
        
        return ScoreResponse(
            score_id=db_score.id,
            resume_id=request.resume_id,
            overall_score=scoring_result['overall_score'],
            section_scores=section_scores_list,
            total_matched_keywords=scoring_result['matched_keywords'],
            total_missing_keywords=scoring_result['missing_keywords'],
            keyword_density=scoring_result['keyword_density'],
            job_title=request.job_title,
            company=request.company,
            scoring_method=scoring_result['scoring_method'],
            created_at=db_score.created_at
        )
        
    except Exception as e:
        logger.error(f"Error scoring resume {request.resume_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to score resume: {str(e)}"
        )


@router.post("/suggestions", response_model=SuggestionResponse)
async def get_resume_suggestions(
    request: ScoreRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get improvement suggestions for a resume based on job description
    
    Args:
        request: ScoreRequest with resume ID and job description
        db: Database session
        
    Returns:
        SuggestionResponse with actionable improvement suggestions
    """
    
    # Get the parsed resume
    result = await db.execute(select(Resume).where(Resume.id == request.resume_id))
    db_resume = result.scalar_one_or_none()
    
    if not db_resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {request.resume_id} not found"
        )
    
    if not db_resume.parsed_data:
        raise HTTPException(
            status_code=400,
            detail="Resume has not been parsed yet"
        )
    
    try:
        logger.info(f"Generating suggestions for resume {request.resume_id}")
        
        # First, score the resume to get detailed analysis
        scoring_result = await ats_scorer.score_resume(
            parsed_resume=db_resume.parsed_data,
            job_description=request.job_description,
            use_sbert=request.use_sbert,
            custom_weights=request.score_weights
        )
        
        # Generate suggestions
        suggestions_list = ats_scorer.generate_suggestions(scoring_result, db_resume.parsed_data)
        
        # Convert to Pydantic models
        suggestions = [
            Suggestion(
                type=sugg['type'],
                priority=sugg['priority'],
                title=sugg['title'],
                description=sugg['description'],
                keywords_to_add=sugg.get('keywords_to_add', [])
            )
            for sugg in suggestions_list
        ]
        
        # Calculate statistics
        total_suggestions = len(suggestions)
        high_priority_count = sum(1 for s in suggestions if s.priority == 'high')
        medium_priority_count = sum(1 for s in suggestions if s.priority == 'medium')
        low_priority_count = sum(1 for s in suggestions if s.priority == 'low')
        
        # Get critical missing keywords
        missing_critical_keywords = scoring_result.get('missing_keywords', [])[:10]
        
        # Check for formatting issues
        formatting_issues = []
        contact_info = db_resume.parsed_data.get('contact_info', {})
        if not contact_info.get('email'):
            formatting_issues.append("Missing email address")
        if not contact_info.get('phone'):
            formatting_issues.append("Missing phone number")
        if not contact_info.get('name'):
            formatting_issues.append("Name not clearly identified")
        
        logger.info(f"Generated {total_suggestions} suggestions for resume {request.resume_id}")
        
        return SuggestionResponse(
            resume_id=request.resume_id,
            suggestions=suggestions,
            total_suggestions=total_suggestions,
            high_priority_count=high_priority_count,
            medium_priority_count=medium_priority_count,
            low_priority_count=low_priority_count,
            missing_critical_keywords=missing_critical_keywords,
            formatting_issues=formatting_issues,
            created_at=db_score.created_at if 'db_score' in locals() else None
        )
        
    except Exception as e:
        logger.error(f"Error generating suggestions for resume {request.resume_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


@router.get("/scores/{score_id}", response_model=ScoreResponse)
async def get_score(
    score_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific score record by ID
    
    Args:
        score_id: UUID of the score record
        db: Database session
        
    Returns:
        ScoreResponse with score details
    """
    
    # Query score
    result = await db.execute(select(ResumeScore).where(ResumeScore.id == score_id))
    db_score = result.scalar_one_or_none()
    
    if not db_score:
        raise HTTPException(
            status_code=404,
            detail=f"Score {score_id} not found"
        )
    
    # Get associated job description
    jd_info = {}
    if db_score.job_description_id:
        jd_result = await db.execute(
            select(JobDescription).where(JobDescription.id == db_score.job_description_id)
        )
        db_jd = jd_result.scalar_one_or_none()
        if db_jd:
            jd_info = {'job_title': db_jd.title, 'company': db_jd.company}
    
    # Format section scores
    section_scores = []
    if db_score.skills_score is not None:
        section_scores.append({
            'section': 'skills',
            'score': db_score.skills_score,
            'matched_keywords': [],  # Could be stored separately if needed
            'missing_keywords': [],
            'weight': 0.4  # Default weight
        })
    
    if db_score.experience_score is not None:
        section_scores.append({
            'section': 'experience',
            'score': db_score.experience_score,
            'matched_keywords': [],
            'missing_keywords': [],
            'weight': 0.35
        })
    
    if db_score.education_score is not None:
        section_scores.append({
            'section': 'education',
            'score': db_score.education_score,
            'matched_keywords': [],
            'missing_keywords': [],
            'weight': 0.25
        })
    
    return ScoreResponse(
        score_id=db_score.id,
        resume_id=db_score.resume_id,
        overall_score=db_score.overall_score,
        section_scores=section_scores,
        total_matched_keywords=db_score.matched_keywords or [],
        total_missing_keywords=db_score.missing_keywords or [],
        keyword_density=0.0,  # Could calculate if needed
        job_title=jd_info.get('job_title'),
        company=jd_info.get('company'),
        scoring_method="tfidf",
        created_at=db_score.created_at
    )


@router.get("/resumes/{resume_id}/scores")
async def get_resume_scores(
    resume_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all score records for a specific resume
    
    Args:
        resume_id: UUID of the resume
        db: Database session
        
    Returns:
        List of score records
    """
    
    # Verify resume exists
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    db_resume = result.scalar_one_or_none()
    
    if not db_resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )
    
    # Get all scores for this resume
    scores_result = await db.execute(
        select(ResumeScore)
        .where(ResumeScore.resume_id == resume_id)
        .order_by(ResumeScore.created_at.desc())
    )
    scores = scores_result.scalars().all()
    
    return {
        "resume_id": resume_id,
        "total_scores": len(scores),
        "scores": [
            {
                "id": score.id,
                "overall_score": score.overall_score,
                "created_at": score.created_at,
                "job_description_id": score.job_description_id
            }
            for score in scores
        ]
    }