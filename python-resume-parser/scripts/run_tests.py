#!/usr/bin/env python3
"""
Test runner for Resume Parser & ATS Scoring System
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def run_backend_tests():
    """Run backend unit tests"""
    print("🧪 Running Backend Tests")
    print("-" * 30)
    
    test_files = [
        "tests/test_resume_parser.py",
        "tests/test_ats_scorer.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\n📝 Running {test_file}...")
            success, stdout, stderr = run_command(f"python -m pytest {test_file} -v")
            
            if success:
                print(f"✅ {test_file} - PASSED")
            else:
                print(f"❌ {test_file} - FAILED")
                print(f"Error: {stderr}")
                all_passed = False
        else:
            print(f"⚠️ {test_file} not found")
    
    return all_passed

def test_api_endpoints():
    """Test API endpoints are working"""
    print("\n🌐 Testing API Endpoints")
    print("-" * 30)
    
    import requests
    import time
    
    # Wait for backend to be ready
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is running")
                break
        except:
            if i < max_retries - 1:
                print(f"⏳ Waiting for backend... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print("❌ Backend not responding")
                return False
    
    # Test endpoints
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/api/v1/resumes", "List resumes"),
        ("GET", "/api/v1/dashboard-data", "Dashboard data")
    ]
    
    all_passed = True
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            
            if response.status_code in [200, 404]:  # 404 is ok for empty lists
                print(f"✅ {description}: {response.status_code}")
            else:
                print(f"❌ {description}: {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {description}: {str(e)}")
            all_passed = False
    
    return all_passed

def test_sample_resume_parsing():
    """Test parsing sample resumes"""
    print("\n📄 Testing Resume Parsing")
    print("-" * 30)
    
    sample_resumes = Path("data/resumes").glob("*.pdf")
    
    for resume_path in sample_resumes:
        print(f"\n📝 Testing {resume_path.name}...")
        
        try:
            import requests
            
            with open(resume_path, 'rb') as f:
                files = {'file': (resume_path.name, f, 'application/pdf')}
                response = requests.post(
                    "http://localhost:8000/api/v1/parse_resume",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Parsed successfully")
                print(f"   - Name: {result.get('contact_info', {}).get('name', 'N/A')}")
                print(f"   - Email: {result.get('contact_info', {}).get('email', 'N/A')}")
                print(f"   - Skills: {len(result.get('skills', {}).get('technical', []))} technical")
            else:
                print(f"❌ Parsing failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing {resume_path.name}: {str(e)}")
            return False
    
    return True

def test_scoring_functionality():
    """Test ATS scoring"""
    print("\n📊 Testing ATS Scoring")
    print("-" * 30)
    
    # First, get a resume ID
    try:
        import requests
        
        response = requests.get("http://localhost:8000/api/v1/resumes", timeout=5)
        if response.status_code != 200:
            print("❌ Cannot get resumes for scoring test")
            return False
        
        resumes = response.json().get('resumes', [])
        if not resumes:
            print("⚠️ No resumes available for scoring test")
            return True
        
        resume_id = resumes[0]['id']
        
        # Test scoring
        scoring_data = {
            "resume_id": resume_id,
            "job_description": """
            Software Engineer position requiring Python, JavaScript, and React experience.
            Looking for candidates with strong technical background and problem-solving skills.
            Experience with cloud platforms like AWS preferred.
            Bachelor's degree in Computer Science or related field required.
            """,
            "job_title": "Software Engineer",
            "company": "Test Company"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/score_resume",
            json=scoring_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Scoring successful")
            print(f"   - Overall Score: {result.get('overall_score', 0):.2%}")
            print(f"   - Matched Keywords: {len(result.get('total_matched_keywords', []))}")
            print(f"   - Missing Keywords: {len(result.get('total_missing_keywords', []))}")
        else:
            print(f"❌ Scoring failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing scoring: {str(e)}")
        return False
    
    return True

def main():
    """Main test runner"""
    print("🧪 Resume Parser & ATS System - Test Suite")
    print("=" * 50)
    
    # Run unit tests
    backend_tests_passed = run_backend_tests()
    
    # Test API endpoints
    api_tests_passed = test_api_endpoints()
    
    # Test resume parsing
    parsing_tests_passed = test_sample_resume_parsing()
    
    # Test scoring
    scoring_tests_passed = test_scoring_functionality()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary")
    print("-" * 20)
    print(f"Backend Unit Tests: {'✅ PASSED' if backend_tests_passed else '❌ FAILED'}")
    print(f"API Endpoints: {'✅ PASSED' if api_tests_passed else '❌ FAILED'}")
    print(f"Resume Parsing: {'✅ PASSED' if parsing_tests_passed else '❌ FAILED'}")
    print(f"ATS Scoring: {'✅ PASSED' if scoring_tests_passed else '❌ FAILED'}")
    
    all_passed = all([backend_tests_passed, api_tests_passed, parsing_tests_passed, scoring_tests_passed])
    
    if all_passed:
        print("\n🎉 All tests PASSED!")
    else:
        print("\n❌ Some tests FAILED!")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)