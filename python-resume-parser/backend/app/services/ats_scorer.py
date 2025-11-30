"""
ATS Scoring service - computes resume-job description similarity and provides suggestions
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
import string
import math

# NLP and ML
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Optional SBERT for enhanced scoring
try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ATSScorerService:
    """Service for ATS scoring and resume improvement suggestions"""
    
    def __init__(self):
        self.setup_nlp()
        self.setup_keywords_database()
        self.setup_scoring_weights()
        
    def setup_nlp(self):
        """Initialize NLP components for text processing"""
        
        # Initialize NLTK components
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
            
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet', quiet=True)
        
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),  # Unigrams and bigrams
            min_df=1,
            max_df=0.95,
            lowercase=True,
            token_pattern=r'[a-zA-Z][a-zA-Z0-9+#./-]*[a-zA-Z0-9+#]|[a-zA-Z]'  # Include tech terms like C++, .NET
        )
        
        # Initialize SBERT if available
        self.sbert_model = None
        if SBERT_AVAILABLE:
            try:
                self.sbert_model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
                logger.info("SBERT model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load SBERT model: {e}")
    
    def setup_keywords_database(self):
        """Setup comprehensive keywords database for various job categories"""
        
        self.job_keywords = {
            'software_engineering': {
                'required': [
                    'programming', 'coding', 'development', 'software', 'application',
                    'algorithm', 'data structure', 'debugging', 'testing', 'version control'
                ],
                'technical_skills': [
                    'python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'ruby',
                    'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask',
                    'mysql', 'postgresql', 'mongodb', 'redis', 'aws', 'azure', 'docker',
                    'kubernetes', 'git', 'jenkins', 'agile', 'scrum', 'rest api', 'graphql'
                ],
                'soft_skills': [
                    'problem solving', 'analytical thinking', 'teamwork', 'communication',
                    'collaboration', 'leadership', 'mentoring', 'code review'
                ]
            },
            'data_science': {
                'required': [
                    'data analysis', 'machine learning', 'statistics', 'modeling',
                    'data visualization', 'analytics', 'insights', 'research'
                ],
                'technical_skills': [
                    'python', 'r', 'sql', 'pandas', 'numpy', 'scikit-learn', 'tensorflow',
                    'pytorch', 'keras', 'matplotlib', 'seaborn', 'tableau', 'power bi',
                    'jupyter', 'spark', 'hadoop', 'aws', 'azure', 'gcp'
                ],
                'soft_skills': [
                    'analytical thinking', 'problem solving', 'communication',
                    'business acumen', 'storytelling', 'presentation'
                ]
            },
            'product_management': {
                'required': [
                    'product strategy', 'roadmap', 'requirements', 'stakeholder',
                    'user experience', 'market research', 'competitive analysis'
                ],
                'technical_skills': [
                    'jira', 'confluence', 'figma', 'sketch', 'analytics', 'sql',
                    'a/b testing', 'user research', 'wireframing', 'prototyping'
                ],
                'soft_skills': [
                    'leadership', 'communication', 'strategic thinking', 'prioritization',
                    'collaboration', 'negotiation', 'influence', 'decision making'
                ]
            },
            'marketing': {
                'required': [
                    'marketing strategy', 'brand management', 'campaign', 'content',
                    'social media', 'digital marketing', 'analytics', 'roi'
                ],
                'technical_skills': [
                    'google analytics', 'facebook ads', 'google ads', 'hubspot',
                    'salesforce', 'mailchimp', 'hootsuite', 'canva', 'photoshop',
                    'seo', 'sem', 'email marketing', 'content management'
                ],
                'soft_skills': [
                    'creativity', 'communication', 'analytical thinking',
                    'project management', 'collaboration', 'adaptability'
                ]
            }
        }
        
        # Action words that indicate impact and achievement
        self.impact_words = [
            'achieved', 'improved', 'increased', 'decreased', 'reduced', 'optimized',
            'streamlined', 'developed', 'created', 'implemented', 'launched', 'led',
            'managed', 'delivered', 'designed', 'built', 'enhanced', 'automated',
            'scaled', 'grew', 'exceeded', 'outperformed', 'transformed', 'innovated'
        ]
        
        # Quantifiable metrics indicators
        self.metrics_patterns = [
            r'\d+%', r'\$\d+', r'\d+x', r'\d+\+', r'\d+ million', r'\d+ thousand',
            r'\d+ users', r'\d+ customers', r'\d+ hours', r'\d+ days', r'\d+ weeks'
        ]
    
    def setup_scoring_weights(self):
        """Setup default scoring weights"""
        self.default_weights = settings.DEFAULT_SCORE_WEIGHTS
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important tech symbols
        # Keep: +, #, ., -, / for terms like C++, C#, .NET, etc.
        text = re.sub(r'[^\w\s+#./-]', ' ', text)
        
        # Normalize common tech terms
        tech_normalizations = {
            'c plus plus': 'c++',
            'c sharp': 'c#',
            'dot net': '.net',
            'javascript': 'js',
            'typescript': 'ts',
            'postgresql': 'postgres',
            'amazon web services': 'aws',
            'google cloud platform': 'gcp'
        }
        
        for old, new in tech_normalizations.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def extract_keywords_from_text(self, text: str, top_n: int = 50) -> List[str]:
        """Extract important keywords from text using TF-IDF"""
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Tokenize and remove stopwords
        tokens = word_tokenize(processed_text)
        tokens = [token for token in tokens if token not in self.stop_words and len(token) > 2]
        
        # Lemmatize tokens
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        # Rejoin for TF-IDF
        clean_text = ' '.join(tokens)
        
        # Use TF-IDF to extract important terms
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([clean_text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords
            keyword_scores = list(zip(feature_names, tfidf_scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            keywords = [keyword for keyword, score in keyword_scores[:top_n] if score > 0]
            return keywords
            
        except Exception as e:
            logger.warning(f"TF-IDF keyword extraction failed: {e}")
            # Fallback to simple frequency analysis
            from collections import Counter
            word_freq = Counter(tokens)
            return [word for word, freq in word_freq.most_common(top_n)]
    
    def compute_tfidf_similarity(self, resume_text: str, jd_text: str) -> float:
        """Compute cosine similarity between resume and job description using TF-IDF"""
        
        try:
            # Preprocess texts
            resume_processed = self.preprocess_text(resume_text)
            jd_processed = self.preprocess_text(jd_text)
            
            # Create TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([resume_processed, jd_processed])
            
            # Compute cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            similarity_score = similarity_matrix[0][1]  # Similarity between resume and JD
            
            return max(0.0, min(1.0, similarity_score))  # Ensure score is between 0 and 1
            
        except Exception as e:
            logger.error(f"TF-IDF similarity computation failed: {e}")
            return 0.0
    
    def compute_sbert_similarity(self, resume_text: str, jd_text: str) -> float:
        """Compute semantic similarity using SBERT embeddings"""
        
        if not self.sbert_model:
            logger.warning("SBERT model not available")
            return 0.0
            
        try:
            # Generate embeddings
            resume_embedding = self.sbert_model.encode([resume_text])
            jd_embedding = self.sbert_model.encode([jd_text])
            
            # Compute cosine similarity
            similarity = cosine_similarity(resume_embedding, jd_embedding)[0][0]
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"SBERT similarity computation failed: {e}")
            return 0.0
    
    def analyze_keyword_match(self, resume_text: str, jd_text: str) -> Tuple[List[str], List[str], float]:
        """Analyze keyword matches between resume and job description"""
        
        # Extract keywords from both texts
        resume_keywords = set(self.extract_keywords_from_text(resume_text, top_n=100))
        jd_keywords = set(self.extract_keywords_from_text(jd_text, top_n=100))
        
        # Find matches
        matched_keywords = list(resume_keywords & jd_keywords)
        missing_keywords = list(jd_keywords - resume_keywords)
        
        # Calculate keyword density
        if len(jd_keywords) > 0:
            keyword_density = len(matched_keywords) / len(jd_keywords)
        else:
            keyword_density = 0.0
        
        return matched_keywords, missing_keywords, keyword_density
    
    def score_section(self, resume_section: str, jd_text: str, section_type: str) -> Dict[str, Any]:
        """Score a specific resume section against job description"""
        
        if not resume_section or not resume_section.strip():
            return {
                'score': 0.0,
                'matched_keywords': [],
                'missing_keywords': [],
                'feedback': f"No {section_type} information found in resume"
            }
        
        # Compute similarity
        similarity_score = self.compute_tfidf_similarity(resume_section, jd_text)
        
        # Analyze keywords
        matched_keywords, missing_keywords, _ = self.analyze_keyword_match(resume_section, jd_text)
        
        # Section-specific adjustments
        if section_type == 'skills':
            # Skills section gets bonus for technical keyword matches
            tech_matches = 0
            for category_data in self.job_keywords.values():
                tech_skills = category_data.get('technical_skills', [])
                resume_lower = resume_section.lower()
                for skill in tech_skills:
                    if skill.lower() in resume_lower:
                        tech_matches += 1
            
            # Boost score based on technical matches
            tech_boost = min(0.3, tech_matches * 0.02)  # Max 30% boost
            similarity_score = min(1.0, similarity_score + tech_boost)
        
        elif section_type == 'experience':
            # Experience section gets bonus for impact words and metrics
            impact_count = sum(1 for word in self.impact_words if word in resume_section.lower())
            metrics_count = sum(1 for pattern in self.metrics_patterns if re.search(pattern, resume_section))
            
            impact_boost = min(0.2, impact_count * 0.02)  # Max 20% boost
            metrics_boost = min(0.2, metrics_count * 0.05)  # Max 20% boost
            similarity_score = min(1.0, similarity_score + impact_boost + metrics_boost)
        
        return {
            'score': similarity_score,
            'matched_keywords': matched_keywords[:10],  # Top 10 matches
            'missing_keywords': missing_keywords[:10],  # Top 10 missing
            'feedback': self.generate_section_feedback(section_type, similarity_score, matched_keywords, missing_keywords)
        }
    
    def generate_section_feedback(self, section_type: str, score: float, matched: List[str], missing: List[str]) -> str:
        """Generate feedback for a specific section"""
        
        if score >= 0.8:
            return f"Excellent {section_type} match with the job requirements."
        elif score >= 0.6:
            feedback = f"Good {section_type} alignment. "
            if missing:
                feedback += f"Consider highlighting: {', '.join(missing[:3])}."
            return feedback
        elif score >= 0.4:
            feedback = f"Moderate {section_type} match. "
            if missing:
                feedback += f"Missing key terms: {', '.join(missing[:5])}."
            return feedback
        else:
            feedback = f"Low {section_type} alignment. "
            if missing:
                feedback += f"Add relevant experience/skills: {', '.join(missing[:5])}."
            return feedback
    
    async def score_resume(self, parsed_resume: Dict[str, Any], job_description: str, 
                          use_sbert: bool = False, custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Main method to score resume against job description"""
        
        try:
            # Use custom weights or defaults
            weights = custom_weights or self.default_weights
            
            # Extract resume text sections
            resume_sections = {
                'skills': self.extract_skills_text(parsed_resume.get('skills', {})),
                'experience': self.extract_experience_text(parsed_resume.get('experience', [])),
                'education': self.extract_education_text(parsed_resume.get('education', []))
            }
            
            # Combine all resume text
            full_resume_text = parsed_resume.get('raw_text', '')
            
            # Compute overall similarity
            if use_sbert:
                overall_score = self.compute_sbert_similarity(full_resume_text, job_description)
                scoring_method = "sbert"
            else:
                overall_score = self.compute_tfidf_similarity(full_resume_text, job_description)
                scoring_method = "tfidf"
            
            # Score individual sections
            section_scores = {}
            for section_name, section_text in resume_sections.items():
                section_result = self.score_section(section_text, job_description, section_name)
                section_scores[section_name] = {
                    'score': section_result['score'],
                    'matched_keywords': section_result['matched_keywords'],
                    'missing_keywords': section_result['missing_keywords'],
                    'weight': weights.get(section_name, 0.0)
                }
            
            # Compute weighted section score
            weighted_score = sum(
                section_scores[section]['score'] * section_scores[section]['weight']
                for section in section_scores
            )
            
            # Combine overall and weighted scores
            final_score = (overall_score * 0.6) + (weighted_score * 0.4)
            
            # Analyze overall keyword match
            matched_keywords, missing_keywords, keyword_density = self.analyze_keyword_match(
                full_resume_text, job_description
            )
            
            return {
                'overall_score': round(final_score, 3),
                'section_scores': section_scores,
                'matched_keywords': matched_keywords[:20],  # Top 20
                'missing_keywords': missing_keywords[:20],  # Top 20
                'keyword_density': round(keyword_density, 3),
                'scoring_method': scoring_method,
                'weights_used': weights
            }
            
        except Exception as e:
            logger.error(f"Error scoring resume: {str(e)}")
            raise
    
    def extract_skills_text(self, skills_data: Dict[str, Any]) -> str:
        """Extract text from skills data structure"""
        skills_text = []
        
        for category, skills_list in skills_data.items():
            if isinstance(skills_list, list):
                skills_text.extend(skills_list)
            elif isinstance(skills_list, str):
                skills_text.append(skills_list)
        
        return ' '.join(skills_text)
    
    def extract_experience_text(self, experience_data: List[Dict[str, Any]]) -> str:
        """Extract text from experience data structure"""
        experience_text = []
        
        for exp in experience_data:
            if isinstance(exp, dict):
                # Add job title and company
                if exp.get('title'):
                    experience_text.append(exp['title'])
                if exp.get('company'):
                    experience_text.append(exp['company'])
                
                # Add description and details
                if exp.get('description'):
                    experience_text.append(exp['description'])
                if exp.get('details') and isinstance(exp['details'], list):
                    experience_text.extend(exp['details'])
        
        return ' '.join(experience_text)
    
    def extract_education_text(self, education_data: List[Dict[str, Any]]) -> str:
        """Extract text from education data structure"""
        education_text = []
        
        for edu in education_data:
            if isinstance(edu, dict):
                # Add institution, degree, field
                if edu.get('institution'):
                    education_text.append(edu['institution'])
                if edu.get('degree'):
                    education_text.append(edu['degree'])
                if edu.get('field_of_study'):
                    education_text.append(edu['field_of_study'])
        
        return ' '.join(education_text)
    
    def generate_suggestions(self, score_data: Dict[str, Any], parsed_resume: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on scoring results"""
        
        suggestions = []
        
        # Overall score-based suggestions
        overall_score = score_data.get('overall_score', 0.0)
        
        if overall_score < 0.3:
            suggestions.append({
                'type': 'overall',
                'priority': 'high',
                'title': 'Low ATS Compatibility',
                'description': 'Your resume has low compatibility with this job. Consider significant restructuring to better match job requirements.',
                'keywords_to_add': score_data.get('missing_keywords', [])[:5]
            })
        elif overall_score < 0.6:
            suggestions.append({
                'type': 'overall',
                'priority': 'medium',
                'title': 'Moderate ATS Score',
                'description': 'Your resume partially matches the job requirements. Focus on adding missing keywords and improving relevant sections.',
                'keywords_to_add': score_data.get('missing_keywords', [])[:3]
            })
        
        # Section-specific suggestions
        section_scores = score_data.get('section_scores', {})
        
        for section_name, section_data in section_scores.items():
            section_score = section_data.get('score', 0.0)
            missing_keywords = section_data.get('missing_keywords', [])
            
            if section_score < 0.4 and missing_keywords:
                suggestions.append({
                    'type': section_name,
                    'priority': 'high',
                    'title': f'Improve {section_name.title()} Section',
                    'description': f'Your {section_name} section needs strengthening. Add relevant keywords and expand details.',
                    'keywords_to_add': missing_keywords[:5]
                })
            elif section_score < 0.7 and missing_keywords:
                suggestions.append({
                    'type': section_name,
                    'priority': 'medium',
                    'title': f'Enhance {section_name.title()} Section',
                    'description': f'Consider adding more relevant {section_name} details to better match job requirements.',
                    'keywords_to_add': missing_keywords[:3]
                })
        
        # Specific improvement suggestions
        self.add_specific_suggestions(suggestions, parsed_resume, score_data)
        
        return suggestions
    
    def add_specific_suggestions(self, suggestions: List[Dict[str, Any]], parsed_resume: Dict[str, Any], score_data: Dict[str, Any]):
        """Add specific, actionable suggestions"""
        
        # Check for quantifiable achievements
        experience_text = self.extract_experience_text(parsed_resume.get('experience', []))
        
        metrics_count = sum(1 for pattern in self.metrics_patterns if re.search(pattern, experience_text))
        impact_count = sum(1 for word in self.impact_words if word in experience_text.lower())
        
        if metrics_count < 2:
            suggestions.append({
                'type': 'experience',
                'priority': 'high',
                'title': 'Add Quantifiable Achievements',
                'description': 'Include specific numbers, percentages, or metrics to demonstrate your impact (e.g., "Increased efficiency by 25%", "Managed team of 10").',
                'keywords_to_add': ['metrics', 'results', 'achievements']
            })
        
        if impact_count < 3:
            suggestions.append({
                'type': 'experience',
                'priority': 'medium',
                'title': 'Use Strong Action Words',
                'description': 'Start bullet points with strong action verbs like "developed", "implemented", "optimized", "led".',
                'keywords_to_add': self.impact_words[:5]
            })
        
        # Check for technical skills coverage
        skills_data = parsed_resume.get('skills', {})
        technical_skills = skills_data.get('technical', [])
        
        if len(technical_skills) < 5:
            suggestions.append({
                'type': 'skills',
                'priority': 'medium',
                'title': 'Expand Technical Skills',
                'description': 'Add more relevant technical skills, tools, and technologies mentioned in the job description.',
                'keywords_to_add': score_data.get('missing_keywords', [])[:3]
            })
        
        # Check contact information
        contact_info = parsed_resume.get('contact_info', {})
        
        if not contact_info.get('linkedin'):
            suggestions.append({
                'type': 'format',
                'priority': 'low',
                'title': 'Add LinkedIn Profile',
                'description': 'Include your LinkedIn profile URL to provide recruiters with additional information.',
                'keywords_to_add': []
            })
        
        if not contact_info.get('email') or not contact_info.get('phone'):
            suggestions.append({
                'type': 'format',
                'priority': 'high',
                'title': 'Complete Contact Information',
                'description': 'Ensure your email and phone number are clearly visible on your resume.',
                'keywords_to_add': []
            })