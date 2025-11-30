import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\hruth\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

"""
FastAPI Backend for Resume Parser & ATS Scoring System
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import os
import tempfile
from pathlib import Path

from app.core.database import init_db
from app.core.config import settings
from app.api import resumes, scoring, dashboard
from app.services.resume_parser import ResumeParserService
from app.services.ats_scorer import ATSScorerService

# Initialize services
resume_parser = ResumeParserService()
ats_scorer = ATSScorerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print("🚀 Starting Resume Parser API...")
    await init_db()
    
    # Download required NLTK data
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        print("✅ NLTK data downloaded")
    except Exception as e:
        print(f"⚠️ NLTK download warning: {e}")
    
    # Download spaCy model if needed
    try:
        import spacy
        try:
            spacy.load("en_core_web_sm")
        except OSError:
            print("📦 Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_sm")
        print("✅ spaCy model ready")
    except Exception as e:
        print(f"⚠️ spaCy model warning: {e}")
    
    print("✅ Resume Parser API ready!")
    yield
    
    # Shutdown
    print("🛑 Shutting down Resume Parser API...")


# Create FastAPI app
app = FastAPI(
    title="Resume Parser & ATS Scoring API",
    description="A complete Python-based Resume Parsing & ATS Scoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resumes.router, prefix="/api/v1", tags=["resumes"])
app.include_router(scoring.router, prefix="/api/v1", tags=["scoring"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Resume Parser & ATS Scoring API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "resume_parser": "active",
            "ats_scorer": "active",
            "database": "connected"
        }
    }

# Backwards-compatible endpoint used by the Streamlit dashboard
@app.get("/api/v1/health")
async def api_v1_health():
    """
    Compatibility route that mirrors /health for dashboards or older clients
    that expect /api/v1/health.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "resume_parser": "active",
            "ats_scorer": "active",
            "database": "connected"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("DEBUG") == "true" else False
    )

