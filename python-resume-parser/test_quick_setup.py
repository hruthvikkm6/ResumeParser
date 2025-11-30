#!/usr/bin/env python3
"""
Quick setup test to verify the system is ready
"""

import sys
from pathlib import Path

def test_imports():
    """Test critical imports work"""
    print("🧪 Testing critical imports...")
    
    try:
        # Test FastAPI backend imports
        sys.path.insert(0, str(Path("backend").absolute()))
        
        from app.services.resume_parser import ResumeParserService
        from app.services.ats_scorer import ATSScorerService
        from app.core.config import settings
        
        print("✅ Backend imports successful")
        
        # Test basic initialization
        parser = ResumeParserService()
        scorer = ATSScorerService()
        
        print("✅ Service initialization successful")
        print(f"✅ Settings loaded: {settings.APP_NAME}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_dependencies():
    """Test required dependencies are available"""
    print("🔍 Testing dependencies...")
    
    required_packages = [
        'fastapi',
        'streamlit', 
        'pdfminer',
        'sklearn',
        'nltk',
        'spacy',
        'plotly',
        'pandas'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            if package == 'pdfminer':
                import pdfminer.high_level
            elif package == 'sklearn':
                import sklearn
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r backend/requirements.txt && pip install -r dashboard/requirements.txt")
        return False
    
    return True

def test_file_structure():
    """Test required files and directories exist"""
    print("📁 Testing file structure...")
    
    required_files = [
        "backend/app/main.py",
        "backend/app/services/resume_parser.py", 
        "backend/app/services/ats_scorer.py",
        "dashboard/app.py",
        "docker-compose.yml",
        "README.md"
    ]
    
    required_dirs = [
        "backend/app",
        "dashboard/pages",
        "data",
        "tests"
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✅ {dir_path}/")
    
    if missing_files or missing_dirs:
        print(f"\n❌ Missing files: {missing_files}")
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 Resume Parser System - Quick Setup Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies), 
        ("Imports", test_imports)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - System is ready!")
        print("\nNext steps:")
        print("1. Quick start: python start_system.py")
        print("2. Or with Docker: docker-compose up --build")
        print("3. Access dashboard: http://localhost:8501")
    else:
        print("❌ Some tests failed - please fix issues above")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)