"""
Tests for ATS Scorer Service
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.ats_scorer import ATSScorerService

class TestATSScorer:
    """Test suite for ATS scoring functionality"""
    
    @pytest.fixture
    def scorer(self):
        """Create scorer instance for testing"""
        return ATSScorerService()
    
    def test_scorer_initialization(self, scorer):
        """Test scorer initializes correctly"""
        assert scorer is not None
        assert hasattr(scorer, 'tfidf_vectorizer')
        assert hasattr(scorer, 'stop_words')
        assert len(scorer.job_keywords) > 0
    
    def test_text_preprocessing(self, scorer):
        """Test text preprocessing"""
        test_text = "Software Engineer with C++ and JavaScript experience"
        processed = scorer.preprocess_text(test_text)
        
        assert processed.islower()
        assert "c++" in processed
        assert "javascript" in processed or "js" in processed
    
    def test_keyword_extraction(self, scorer):
        """Test keyword extraction from text"""
        test_text = """
        Software Engineer with 5 years experience in Python, React, AWS.
        Developed scalable web applications and led cross-functional teams.
        Strong background in machine learning and data analysis.
        """
        
        keywords = scorer.extract_keywords_from_text(test_text, top_n=20)
        
        assert len(keywords) > 0
        assert any('python' in kw.lower() for kw in keywords)
        assert any('react' in kw.lower() for kw in keywords)
    
    def test_tfidf_similarity(self, scorer):
        """Test TF-IDF similarity computation"""
        resume_text = """
        Software Engineer with Python, React, and AWS experience.
        Built scalable web applications serving millions of users.
        """
        
        jd_text = """
        We are seeking a Software Engineer with Python and React experience.
        Experience with cloud platforms like AWS preferred.
        """
        
        similarity = scorer.compute_tfidf_similarity(resume_text, jd_text)
        
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.1  # Should have some similarity
    
    def test_keyword_analysis(self, scorer):
        """Test keyword matching analysis"""
        resume_text = "Python developer with React and Node.js experience"
        jd_text = "Looking for Python developer with React, Angular, and AWS skills"
        
        matched, missing, density = scorer.analyze_keyword_match(resume_text, jd_text)
        
        assert isinstance(matched, list)
        assert isinstance(missing, list)
        assert 0.0 <= density <= 1.0
        
        # Should match on python and react
        matched_lower = [kw.lower() for kw in matched]
        assert any('python' in kw for kw in matched_lower)
        assert any('react' in kw for kw in matched_lower)
        
        # Should miss AWS
        missing_lower = [kw.lower() for kw in missing]
        assert any('aws' in kw for kw in missing_lower)
    
    def test_section_scoring(self, scorer):
        """Test section-specific scoring"""
        resume_section = """
        Technical Skills: Python, JavaScript, React, Node.js, AWS, Docker
        Machine Learning: TensorFlow, scikit-learn, pandas
        """
        
        jd_text = """
        Requirements: Python, React, AWS experience required.
        Machine learning knowledge preferred.
        """
        
        result = scorer.score_section(resume_section, jd_text, 'skills')
        
        assert 'score' in result
        assert 'matched_keywords' in result
        assert 'missing_keywords' in result
        assert 'feedback' in result
        assert 0.0 <= result['score'] <= 1.0
    
    async def test_full_resume_scoring(self, scorer):
        """Test complete resume scoring"""
        sample_resume = {
            'skills': {
                'technical': ['Python', 'React', 'AWS', 'Docker'],
                'soft': ['Leadership', 'Communication']
            },
            'experience': [
                {
                    'title': 'Software Engineer',
                    'company': 'Tech Corp',
                    'details': ['Developed web applications', 'Led team of 5']
                }
            ],
            'education': [
                {
                    'institution': 'Stanford University',
                    'degree': 'BS Computer Science'
                }
            ],
            'raw_text': """
            John Doe Software Engineer
            Skills: Python, React, AWS, Docker
            Experience: Software Engineer at Tech Corp
            Education: BS Computer Science, Stanford University
            """
        }
        
        job_description = """
        Software Engineer position requiring Python, React, and AWS experience.
        Looking for candidates with strong technical background and leadership skills.
        Computer Science degree preferred.
        """
        
        result = await scorer.score_resume(sample_resume, job_description)
        
        assert 'overall_score' in result
        assert 'section_scores' in result
        assert 'matched_keywords' in result
        assert 'missing_keywords' in result
        assert 'keyword_density' in result
        
        assert 0.0 <= result['overall_score'] <= 1.0
        assert result['overall_score'] > 0.2  # Should have reasonable similarity
        
        # Check section scores
        section_names = {score['section'] for score in result['section_scores'].values()}
        assert 'skills' in section_names
        assert 'experience' in section_names
        assert 'education' in section_names
    
    def test_suggestions_generation(self, scorer):
        """Test improvement suggestions generation"""
        sample_score_data = {
            'overall_score': 0.4,
            'section_scores': {
                'skills': {
                    'score': 0.3,
                    'missing_keywords': ['kubernetes', 'microservices', 'graphql']
                },
                'experience': {
                    'score': 0.5, 
                    'missing_keywords': ['agile', 'scrum', 'leadership']
                }
            },
            'missing_keywords': ['kubernetes', 'microservices', 'agile', 'devops']
        }
        
        sample_resume = {
            'experience': [
                {
                    'title': 'Developer',
                    'details': ['Built applications', 'Fixed bugs']
                }
            ]
        }
        
        suggestions = scorer.generate_suggestions(sample_score_data, sample_resume)
        
        assert len(suggestions) > 0
        
        # Check suggestion structure
        for suggestion in suggestions:
            assert 'type' in suggestion
            assert 'priority' in suggestion
            assert 'title' in suggestion
            assert 'description' in suggestion
            assert suggestion['priority'] in ['high', 'medium', 'low']
        
        # Should have suggestions for low overall score
        priorities = [s['priority'] for s in suggestions]
        assert 'high' in priorities or 'medium' in priorities
    
    def test_impact_words_detection(self, scorer):
        """Test detection of impact words in experience"""
        experience_with_impact = """
        Developed scalable applications serving 1M+ users
        Improved system performance by 40%
        Led cross-functional team of 8 engineers
        Implemented automated testing reducing bugs by 60%
        """
        
        experience_without_impact = """
        Worked on web applications
        Fixed various bugs
        Attended team meetings
        Wrote some code
        """
        
        # Count impact words
        impact_count_good = sum(1 for word in scorer.impact_words if word in experience_with_impact.lower())
        impact_count_bad = sum(1 for word in scorer.impact_words if word in experience_without_impact.lower())
        
        assert impact_count_good > impact_count_bad
        assert impact_count_good >= 3  # Should find "developed", "improved", "led", "implemented"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])