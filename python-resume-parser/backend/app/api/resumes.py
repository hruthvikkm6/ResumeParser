"""
Resume API endpoints for parsing and management
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, Resume
from app.models.resume import ParsedResumeResponse, ResumeResponse, ResumeList
from app.services.resume_parser import ResumeParserService
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize resume parser service
resume_parser = ResumeParserService()


@router.post("/parse_resume", response_model=ParsedResumeResponse)
async def parse_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Parse a PDF resume and extract structured information
    
    Args:
        file: PDF file to parse
        db: Database session
        
    Returns:
        ParsedResumeResponse with extracted resume data
    """
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Create temporary file for processing
    temp_file = None
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(exist_ok=True)
        
        # Create temporary file
        temp_fd, temp_file = tempfile.mkstemp(suffix='.pdf', dir=upload_dir)
        
        # Write uploaded content to temp file
        content = await file.read()
        with os.fdopen(temp_fd, 'wb') as f:
            f.write(content)
        
        logger.info(f"Processing resume file: {file.filename}")
        
        # Parse the resume
        parsed_data = await resume_parser.parse_resume(temp_file, file.filename)
        
        # Save to database
        resume_id = str(uuid.uuid4())
        
        # Create database record
        db_resume = Resume(
            id=resume_id,
            filename=file.filename,
            file_path=temp_file,
            name=parsed_data['contact_info'].get('name'),
            email=parsed_data['contact_info'].get('email'),
            phone=parsed_data['contact_info'].get('phone'),
            skills=parsed_data['skills'],
            experience=parsed_data['experience'],
            education=parsed_data['education'],
            raw_text=parsed_data['raw_text'],
            parsed_data=parsed_data
        )
        
        db.add(db_resume)
        await db.commit()
        await db.refresh(db_resume)
        
        logger.info(f"Successfully parsed and saved resume: {resume_id}")
        
        # Return structured response
        return ParsedResumeResponse(
            id=db_resume.id,
            filename=db_resume.filename,
            contact_info=parsed_data['contact_info'],
            skills=parsed_data['skills'],
            education=parsed_data['education'],
            experience=parsed_data['experience'],
            projects=parsed_data.get('projects', []),
            raw_text=parsed_data['raw_text'],
            created_at=db_resume.created_at
        )
        
    except Exception as e:
        logger.error(f"Error parsing resume {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse resume: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")


@router.get("/resumes/{resume_id}", response_model=ParsedResumeResponse)
async def get_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a parsed resume by ID
    
    Args:
        resume_id: UUID of the resume
        db: Database session
        
    Returns:
        ParsedResumeResponse with resume data
    """
    
    # Query database
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    db_resume = result.scalar_one_or_none()
    
    if not db_resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )
    
    # Extract parsed data
    parsed_data = db_resume.parsed_data or {}
    
    return ParsedResumeResponse(
        id=db_resume.id,
        filename=db_resume.filename,
        contact_info=parsed_data.get('contact_info', {}),
        skills=parsed_data.get('skills', {}),
        education=parsed_data.get('education', []),
        experience=parsed_data.get('experience', []),
        projects=parsed_data.get('projects', []),
        raw_text=db_resume.raw_text or '',
        created_at=db_resume.created_at
    )


@router.get("/resumes", response_model=ResumeList)
async def list_resumes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all parsed resumes with pagination
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        
    Returns:
        ResumeList with paginated resume data
    """
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query resumes with pagination
    result = await db.execute(
        select(Resume)
        .order_by(Resume.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    resumes = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(select(Resume.id))
    total = len(count_result.scalars().all())
    
    # Convert to response format
    resume_responses = [
        ResumeResponse(
            id=resume.id,
            filename=resume.filename,
            name=resume.name,
            email=resume.email,
            phone=resume.phone,
            created_at=resume.created_at
        )
        for resume in resumes
    ]
    
    return ResumeList(
        resumes=resume_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/resumes/{resume_id}")
async def delete_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a resume by ID
    
    Args:
        resume_id: UUID of the resume to delete
        db: Database session
        
    Returns:
        Success message
    """
    
    # Query resume
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    db_resume = result.scalar_one_or_none()
    
    if not db_resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )
    
    # Delete associated file if it exists
    if db_resume.file_path and os.path.exists(db_resume.file_path):
        try:
            os.unlink(db_resume.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {db_resume.file_path}: {e}")
    
    # Delete from database
    await db.delete(db_resume)
    await db.commit()
    
    logger.info(f"Successfully deleted resume: {resume_id}")
    
    return {"message": f"Resume {resume_id} deleted successfully"}


@router.get("/resumes/{resume_id}/raw")
async def get_resume_raw_text(
    resume_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get raw text of a parsed resume
    
    Args:
        resume_id: UUID of the resume
        db: Database session
        
    Returns:
        Raw text content
    """
    
    # Query resume
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    db_resume = result.scalar_one_or_none()
    
    if not db_resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )
    
    return {
        "id": db_resume.id,
        "filename": db_resume.filename,
        "raw_text": db_resume.raw_text or "",
        "character_count": len(db_resume.raw_text) if db_resume.raw_text else 0
    }


@router.post("/resumes/{resume_id}/reparse", response_model=ParsedResumeResponse)
async def reparse_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Reparse an existing resume (useful after parser improvements)
    
    Args:
        resume_id: UUID of the resume to reparse
        db: Database session
        
    Returns:
        ParsedResumeResponse with updated data
    """
    
    # Query resume
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    db_resume = result.scalar_one_or_none()
    
    if not db_resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume {resume_id} not found"
        )
    
    if not db_resume.file_path or not os.path.exists(db_resume.file_path):
        raise HTTPException(
            status_code=400,
            detail="Original file not available for reparsing"
        )
    
    try:
        # Reparse the resume
        parsed_data = await resume_parser.parse_resume(db_resume.file_path, db_resume.filename)
        
        # Update database record
        db_resume.name = parsed_data['contact_info'].get('name')
        db_resume.email = parsed_data['contact_info'].get('email')
        db_resume.phone = parsed_data['contact_info'].get('phone')
        db_resume.skills = parsed_data['skills']
        db_resume.experience = parsed_data['experience']
        db_resume.education = parsed_data['education']
        db_resume.raw_text = parsed_data['raw_text']
        db_resume.parsed_data = parsed_data
        
        await db.commit()
        await db.refresh(db_resume)
        
        logger.info(f"Successfully reparsed resume: {resume_id}")
        
        # Return updated response
        return ParsedResumeResponse(
            id=db_resume.id,
            filename=db_resume.filename,
            contact_info=parsed_data['contact_info'],
            skills=parsed_data['skills'],
            education=parsed_data['education'],
            experience=parsed_data['experience'],
            projects=parsed_data.get('projects', []),
            raw_text=parsed_data['raw_text'],
            created_at=db_resume.created_at
        )
        
    except Exception as e:
        logger.error(f"Error reparsing resume {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reparse resume: {str(e)}"
        )