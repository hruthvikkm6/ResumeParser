#!/usr/bin/env python3
"""
Setup script for Resume Parser & ATS Scoring System
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running: {cmd}")
            print(f"Error output: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running {cmd}: {e}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required. Current version:", f"{version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_system_dependencies():
    """Check system dependencies"""
    print("🔍 Checking system dependencies...")
    
    # Check tesseract
    if not run_command("tesseract --version"):
        print("❌ Tesseract OCR not found. Please install:")
        if platform.system() == "Darwin":  # macOS
            print("   brew install tesseract")
        elif platform.system() == "Linux":
            print("   sudo apt-get install tesseract-ocr")
        elif platform.system() == "Windows":
            print("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        return False
    else:
        print("✅ Tesseract OCR found")
    
    # Check poppler (for pdf2image)
    if platform.system() == "Darwin":
        if not run_command("brew list poppler"):
            print("❌ Poppler not found. Install with: brew install poppler")
            return False
    elif platform.system() == "Linux":
        if not run_command("pkg-config --exists poppler"):
            print("❌ Poppler not found. Install with: sudo apt-get install poppler-utils")
            return False
    
    print("✅ All system dependencies found")
    return True

def setup_backend():
    """Setup backend dependencies"""
    print("\n🔧 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Install Python dependencies
    print("📦 Installing Python dependencies...")
    if not run_command("pip install -r requirements.txt", cwd="backend"):
        print("❌ Failed to install backend dependencies")
        return False
    
    # Download NLTK data
    print("📚 Downloading NLTK data...")
    nltk_commands = [
        "python -c \"import nltk; nltk.download('punkt', quiet=True)\"",
        "python -c \"import nltk; nltk.download('stopwords', quiet=True)\"", 
        "python -c \"import nltk; nltk.download('wordnet', quiet=True)\""
    ]
    
    for cmd in nltk_commands:
        if not run_command(cmd, cwd="backend"):
            print(f"⚠️ Warning: Failed to download NLTK data: {cmd}")
    
    # Download spaCy model
    print("🧠 Downloading spaCy model...")
    if not run_command("python -m spacy download en_core_web_sm", cwd="backend"):
        print("⚠️ Warning: Failed to download spaCy model")
    
    print("✅ Backend setup complete")
    return True

def setup_dashboard():
    """Setup dashboard dependencies"""
    print("\n🎨 Setting up dashboard...")
    
    dashboard_dir = Path("dashboard")
    if not dashboard_dir.exists():
        print("❌ Dashboard directory not found")
        return False
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", cwd="dashboard"):
        print("❌ Failed to install dashboard dependencies")
        return False
    
    print("✅ Dashboard setup complete")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "backend/uploads",
        "data/resumes", 
        "data/processed",
        "logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")

def copy_sample_data():
    """Copy sample resume files"""
    print("\n📄 Setting up sample data...")
    
    # Create sample resume directory if it doesn't exist
    sample_dir = Path("data/resumes")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy existing sample resumes from public directory
    public_resumes = Path("../public/resume-example")
    if public_resumes.exists():
        import shutil
        for resume_file in public_resumes.glob("*.pdf"):
            dest = sample_dir / resume_file.name
            shutil.copy2(resume_file, dest)
            print(f"✅ Copied: {resume_file.name}")
    else:
        print("⚠️ No sample resumes found in ../public/resume-example/")
    
    print("✅ Sample data setup complete")

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running tests...")
    
    test_commands = [
        "python -m pytest tests/test_resume_parser.py::TestResumeParser::test_parser_initialization -v",
        "python -m pytest tests/test_ats_scorer.py::TestATSScorer::test_scorer_initialization -v"
    ]
    
    for cmd in test_commands:
        if run_command(cmd):
            print(f"✅ Test passed: {cmd.split('::')[-1]}")
        else:
            print(f"⚠️ Test failed: {cmd.split('::')[-1]}")

def create_env_file():
    """Create .env file with default settings"""
    print("\n⚙️ Creating environment file...")
    
    env_content = """# Resume Parser & ATS Scoring System Environment Configuration

# Application Settings
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=sqlite+aiosqlite:///./resumes.db

# File Upload Settings
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads

# ML Models
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
SPACY_MODEL=en_core_web_sm

# API Settings
BACKEND_URL=http://localhost:8000

# Scoring Weights (must sum to 1.0)
SKILLS_WEIGHT=0.4
EXPERIENCE_WEIGHT=0.35
EDUCATION_WEIGHT=0.25
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        env_file.write_text(env_content)
        print("✅ Created .env file")
    else:
        print("⚠️ .env file already exists, skipping")

def main():
    """Main setup function"""
    print("🚀 Resume Parser & ATS Scoring System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check system dependencies
    if not check_system_dependencies():
        print("\n❌ Please install system dependencies and run setup again")
        return False
    
    # Create directories
    create_directories()
    
    # Create env file
    create_env_file()
    
    # Setup backend
    if not setup_backend():
        return False
    
    # Setup dashboard
    if not setup_dashboard():
        return False
    
    # Copy sample data
    copy_sample_data()
    
    # Run basic tests
    run_tests()
    
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Start the backend: cd backend && uvicorn app.main:app --reload")
    print("2. Start the dashboard: cd dashboard && streamlit run app.py")
    print("3. Or use Docker: docker-compose up --build")
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Dashboard: http://localhost:8501")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)