"""
Tests for Resume Parser Service
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.resume_parser import ResumeParserService

class TestResumeParser:
    """Test suite for resume parsing functionality"""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for testing"""
        return ResumeParserService()
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly"""
        assert parser is not None
        assert hasattr(parser, 'nlp')
        assert hasattr(parser, 'email_pattern')
        assert hasattr(parser, 'phone_pattern')
        assert len(parser.all_technical_skills) > 0
    
    def test_email_extraction(self, parser):
        """Test email pattern matching"""
        test_text = "Contact John Doe at john.doe@company.com for more information"
        
        match = parser.email_pattern.search(test_text)
        assert match is not None
        assert match.group() == "john.doe@company.com"
    
    def test_phone_extraction(self, parser):
        """Test phone pattern matching"""
        test_cases = [
            "(123) 456-7890",
            "123-456-7890", 
            "123 456 7890",
            "+1-123-456-7890"
        ]
        
        for phone in test_cases:
            match = parser.phone_pattern.search(phone)
            assert match is not None, f"Failed to match phone: {phone}"
    
    def test_skills_extraction(self, parser):
        """Test skills extraction from text"""
        test_text = """
        Skills: Python, Java, React, Node.js, AWS, Docker, Machine Learning,
        Communication, Leadership, Team Management
        """
        
        skills = parser.extract_skills([], test_text)
        
        assert 'python' in [s.lower() for s in skills['technical']]
        assert 'java' in [s.lower() for s in skills['technical']]
        assert 'react' in [s.lower() for s in skills['technical']]
    
    def test_section_identification(self, parser):
        """Test section identification in resume text"""
        test_text = """
        EDUCATION
        University of California, Berkeley
        Bachelor of Science in Computer Science
        
        WORK EXPERIENCE
        Software Engineer at Google
        Developed scalable web applications
        
        SKILLS
        Python, JavaScript, React, AWS
        """
        
        sections = parser.identify_sections(test_text)
        
        assert 'education' in sections
        assert 'experience' in sections  
        assert 'skills' in sections
    
    def test_contact_info_extraction(self, parser):
        """Test contact information extraction"""
        test_text = """
        John Doe
        john.doe@email.com
        (555) 123-4567
        San Francisco, CA
        """
        
        contact_info = parser.extract_contact_info(test_text)
        
        assert contact_info['email'] == "john.doe@email.com"
        assert "(555) 123-4567" in contact_info['phone']
        assert contact_info['name'] == "John Doe"
    
    def test_text_cleaning(self, parser):
        """Test text cleaning functionality"""
        dirty_text = "This  is   a  test\n\n\nwith   extra\t\tspaces"
        clean_text = parser.clean_extracted_text(dirty_text)
        
        assert "  " not in clean_text  # No double spaces
        assert "\n\n" not in clean_text  # No double newlines
        assert "\t" not in clean_text  # No tabs
    
    def test_education_extraction(self, parser):
        """Test education information extraction"""
        education_text = [
            "Stanford University",
            "Bachelor of Science in Computer Science", 
            "GPA: 3.8",
            "Graduated: May 2020"
        ]
        
        education = parser.extract_education(education_text, "")
        
        assert len(education) > 0
        # Check if any education entry has relevant fields
        has_institution = any(edu.get('institution') for edu in education)
        has_degree = any(edu.get('degree') for edu in education)
        
        assert has_institution or has_degree
    
    def test_experience_extraction(self, parser):
        """Test work experience extraction"""
        experience_text = [
            "Software Engineer",
            "Google Inc",
            "June 2020 - Present",
            "• Developed scalable web applications",
            "• Led team of 5 engineers",
            "• Improved performance by 40%"
        ]
        
        experience = parser.extract_experience(experience_text, "")
        
        assert len(experience) > 0
        # Check if any experience entry has relevant fields
        has_title = any(exp.get('title') for exp in experience)
        has_company = any(exp.get('company') for exp in experience)
        has_details = any(exp.get('details') for exp in experience)
        
        assert has_title or has_company or has_details

# Integration test (requires sample PDF)
class TestResumeParserIntegration:
    """Integration tests with actual PDF files"""
    
    @pytest.fixture
    def parser(self):
        return ResumeParserService()
    
    @pytest.mark.skipif(
        not os.path.exists("../public/resume-example/openresume-resume.pdf"),
        reason="Sample PDF not found"
    )
    async def test_parse_sample_pdf(self, parser):
        """Test parsing actual PDF file"""
        pdf_path = "../public/resume-example/openresume-resume.pdf"
        
        if os.path.exists(pdf_path):
            try:
                result = await parser.parse_resume(pdf_path, "sample.pdf")
                
                assert result is not None
                assert 'contact_info' in result
                assert 'skills' in result
                assert 'experience' in result
                assert 'education' in result
                assert 'raw_text' in result
                
                # Check if meaningful data was extracted
                assert len(result['raw_text']) > 100
                
            except Exception as e:
                pytest.fail(f"PDF parsing failed: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])