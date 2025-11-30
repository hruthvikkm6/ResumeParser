"""
Dashboard API endpoints for analytics and summary data
"""

import logging
from typing import Dict, List, Any
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import APIRouter, Depends

from app.core.database import get_db, Resume, ResumeScore, JobDescription
from app.models.scoring import ScoringSummary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard-data", response_model=ScoringSummary)
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    """
    Get summary statistics for the recruiter dashboard
    
    Args:
        db: Database session
        
    Returns:
        ScoringSummary with dashboard analytics
    """
    
    try:
        # Get total resumes count
        total_resumes_result = await db.execute(select(func.count(Resume.id)))
        total_resumes = total_resumes_result.scalar() or 0
        
        # Get average score
        avg_score_result = await db.execute(select(func.avg(ResumeScore.overall_score)))
        average_score = avg_score_result.scalar() or 0.0
        
        # Get score distribution
        scores_result = await db.execute(select(ResumeScore.overall_score))
        scores = [score for score in scores_result.scalars() if score is not None]
        
        score_distribution = {
            "0.0-0.2": sum(1 for s in scores if 0.0 <= s < 0.2),
            "0.2-0.4": sum(1 for s in scores if 0.2 <= s < 0.4),
            "0.4-0.6": sum(1 for s in scores if 0.4 <= s < 0.6),
            "0.6-0.8": sum(1 for s in scores if 0.6 <= s < 0.8),
            "0.8-1.0": sum(1 for s in scores if 0.8 <= s <= 1.0)
        }
        
        # Get common missing skills (from missing_keywords)
        missing_keywords_result = await db.execute(select(ResumeScore.missing_keywords))
        all_missing_keywords = []
        
        for missing_keywords in missing_keywords_result.scalars():
            if missing_keywords and isinstance(missing_keywords, list):
                all_missing_keywords.extend(missing_keywords)
        
        missing_skills_counter = Counter(all_missing_keywords)
        common_missing_skills = [
            {"skill": skill, "frequency": count}
            for skill, count in missing_skills_counter.most_common(10)
        ]
        
        # Get top performing resumes
        top_resumes_result = await db.execute(
            select(Resume.id, Resume.filename, Resume.name, ResumeScore.overall_score)
            .join(ResumeScore, Resume.id == ResumeScore.resume_id)
            .order_by(ResumeScore.overall_score.desc())
            .limit(5)
        )
        
        top_performing_resumes = [
            {
                "resume_id": row[0],
                "filename": row[1],
                "name": row[2] or "Unknown",
                "score": row[3]
            }
            for row in top_resumes_result.fetchall()
        ]
        
        # Get recent activity (last 10 scores)
        recent_activity_result = await db.execute(
            select(Resume.filename, Resume.name, ResumeScore.overall_score, ResumeScore.created_at)
            .join(ResumeScore, Resume.id == ResumeScore.resume_id)
            .order_by(ResumeScore.created_at.desc())
            .limit(10)
        )
        
        recent_activity = [
            {
                "filename": row[0],
                "name": row[1] or "Unknown",
                "score": row[2],
                "timestamp": row[3].isoformat()
            }
            for row in recent_activity_result.fetchall()
        ]
        
        logger.info(f"Generated dashboard data: {total_resumes} resumes, avg score: {average_score:.3f}")
        
        return ScoringSummary(
            total_resumes=total_resumes,
            average_score=round(average_score, 3),
            score_distribution=score_distribution,
            common_missing_skills=common_missing_skills,
            top_performing_resumes=top_performing_resumes,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Error generating dashboard data: {str(e)}")
        # Return empty data structure on error
        return ScoringSummary(
            total_resumes=0,
            average_score=0.0,
            score_distribution={"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0},
            common_missing_skills=[],
            top_performing_resumes=[],
            recent_activity=[]
        )


@router.get("/analytics/skills-analysis")
async def get_skills_analysis(db: AsyncSession = Depends(get_db)):
    """
    Get detailed skills analysis across all resumes
    
    Returns:
        Detailed skills analytics
    """
    
    try:
        # Get all resumes with skills data
        resumes_result = await db.execute(select(Resume.skills).where(Resume.skills.isnot(None)))
        
        # Aggregate skills data
        all_technical_skills = []
        all_soft_skills = []
        all_certifications = []
        
        for skills_data in resumes_result.scalars():
            if isinstance(skills_data, dict):
                technical = skills_data.get('technical', [])
                soft = skills_data.get('soft', [])
                certifications = skills_data.get('certifications', [])
                
                if isinstance(technical, list):
                    all_technical_skills.extend([skill.lower() for skill in technical])
                if isinstance(soft, list):
                    all_soft_skills.extend([skill.lower() for skill in soft])
                if isinstance(certifications, list):
                    all_certifications.extend([cert.lower() for cert in certifications])
        
        # Count frequencies
        technical_counter = Counter(all_technical_skills)
        soft_counter = Counter(all_soft_skills)
        cert_counter = Counter(all_certifications)
        
        return {
            "most_common_technical_skills": [
                {"skill": skill, "count": count}
                for skill, count in technical_counter.most_common(15)
            ],
            "most_common_soft_skills": [
                {"skill": skill, "count": count}
                for skill, count in soft_counter.most_common(10)
            ],
            "most_common_certifications": [
                {"certification": cert, "count": count}
                for cert, count in cert_counter.most_common(10)
            ],
            "total_unique_technical_skills": len(technical_counter),
            "total_unique_soft_skills": len(soft_counter),
            "total_unique_certifications": len(cert_counter)
        }
        
    except Exception as e:
        logger.error(f"Error in skills analysis: {str(e)}")
        return {
            "most_common_technical_skills": [],
            "most_common_soft_skills": [],
            "most_common_certifications": [],
            "total_unique_technical_skills": 0,
            "total_unique_soft_skills": 0,
            "total_unique_certifications": 0
        }


@router.get("/analytics/scoring-trends")
async def get_scoring_trends(db: AsyncSession = Depends(get_db)):
    """
    Get scoring trends over time
    
    Returns:
        Scoring trends and patterns
    """
    
    try:
        # Get scores over time
        scores_result = await db.execute(
            select(ResumeScore.overall_score, ResumeScore.created_at)
            .order_by(ResumeScore.created_at)
        )
        
        scores_data = [(score, created_at) for score, created_at in scores_result.fetchall()]
        
        # Group by date (simplified - group by day)
        from collections import defaultdict
        daily_scores = defaultdict(list)
        
        for score, timestamp in scores_data:
            date_key = timestamp.date().isoformat()
            daily_scores[date_key].append(score)
        
        # Calculate daily averages
        daily_averages = [
            {
                "date": date,
                "average_score": sum(scores) / len(scores),
                "total_resumes": len(scores),
                "max_score": max(scores),
                "min_score": min(scores)
            }
            for date, scores in daily_scores.items()
        ]
        
        # Sort by date
        daily_averages.sort(key=lambda x: x["date"])
        
        return {
            "daily_trends": daily_averages,
            "total_data_points": len(scores_data),
            "date_range": {
                "start": daily_averages[0]["date"] if daily_averages else None,
                "end": daily_averages[-1]["date"] if daily_averages else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error in scoring trends analysis: {str(e)}")
        return {
            "daily_trends": [],
            "total_data_points": 0,
            "date_range": {"start": None, "end": None}
        }


@router.get("/job-descriptions", response_model=List[Dict[str, Any]])
async def list_job_descriptions(db: AsyncSession = Depends(get_db)):
    """
    List all stored job descriptions
    
    Returns:
        List of job descriptions
    """
    
    try:
        result = await db.execute(
            select(JobDescription.id, JobDescription.title, JobDescription.company, JobDescription.created_at)
            .order_by(JobDescription.created_at.desc())
        )
        
        job_descriptions = [
            {
                "id": row[0],
                "title": row[1],
                "company": row[2],
                "created_at": row[3].isoformat()
            }
            for row in result.fetchall()
        ]
        
        return job_descriptions
        
    except Exception as e:
        logger.error(f"Error listing job descriptions: {str(e)}")
        return []


@router.post("/upload_jd")
async def upload_job_description(
    job_description: str,
    title: str = "Untitled Position",
    company: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Save a job description for future use
    
    Args:
        job_description: Job description text
        title: Job title
        company: Company name
        db: Database session
        
    Returns:
        Created job description info
    """
    
    try:
        import uuid
        
        # Create job description record
        db_jd = JobDescription(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            description=job_description
        )
        
        db.add(db_jd)
        await db.commit()
        await db.refresh(db_jd)
        
        logger.info(f"Saved job description: {title} at {company}")
        
        return {
            "id": db_jd.id,
            "title": db_jd.title,
            "company": db_jd.company,
            "created_at": db_jd.created_at.isoformat(),
            "message": "Job description saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error saving job description: {str(e)}")
        return {"error": f"Failed to save job description: {str(e)}"}


@router.get("/export/resume-data/{resume_id}")
async def export_resume_data(
    resume_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """
    Export resume data in various formats
    
    Args:
        resume_id: UUID of the resume
        format: Export format (json, csv)
        db: Database session
        
    Returns:
        Exported resume data
    """
    
    # Get resume with all associated scores
    resume_result = await db.execute(select(Resume).where(Resume.id == resume_id))
    db_resume = resume_result.scalar_one_or_none()
    
    if not db_resume:
        return {"error": "Resume not found"}
    
    # Get all scores for this resume
    scores_result = await db.execute(
        select(ResumeScore).where(ResumeScore.resume_id == resume_id)
    )
    scores = scores_result.scalars().all()
    
    export_data = {
        "resume_info": {
            "id": db_resume.id,
            "filename": db_resume.filename,
            "name": db_resume.name,
            "email": db_resume.email,
            "phone": db_resume.phone,
            "created_at": db_resume.created_at.isoformat()
        },
        "parsed_data": db_resume.parsed_data,
        "scores": [
            {
                "id": score.id,
                "overall_score": score.overall_score,
                "skills_score": score.skills_score,
                "experience_score": score.experience_score,
                "education_score": score.education_score,
                "matched_keywords": score.matched_keywords,
                "missing_keywords": score.missing_keywords,
                "created_at": score.created_at.isoformat()
            }
            for score in scores
        ]
    }
    
    if format.lower() == "csv":
        # Flatten data for CSV export
        import json
        flattened_data = {
            "resume_id": db_resume.id,
            "filename": db_resume.filename,
            "name": db_resume.name,
            "email": db_resume.email,
            "phone": db_resume.phone,
            "skills": json.dumps(db_resume.parsed_data.get('skills', {}) if db_resume.parsed_data else {}),
            "total_scores": len(scores),
            "average_score": sum(s.overall_score for s in scores) / len(scores) if scores else 0,
            "created_at": db_resume.created_at.isoformat()
        }
        return {"format": "csv", "data": flattened_data}
    
    return {"format": "json", "data": export_data}