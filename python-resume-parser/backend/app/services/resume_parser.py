"""
Resume parsing service - extracts structured data from PDF resumes
"""

import re
import tempfile
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

# PDF processing
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import pdf2image
import pytesseract
from PIL import Image

# NLP
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import string

# Date parsing
from dateutil import parser as date_parser

from app.models.resume import ContactInfo, Education, Experience, Project, Skills
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeParserService:
    """Service for parsing PDF resumes and extracting structured information"""
    
    def __init__(self):
        self.setup_nlp()
        self.setup_patterns()
        self.setup_skills_database()
    
    def setup_nlp(self):
        """Initialize NLP components"""
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
        except OSError:
            logger.warning(f"spaCy model {settings.SPACY_MODEL} not found. Using basic processing.")
            self.nlp = None
            
        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
            
        self.stop_words = set(stopwords.words('english'))
    
    def setup_patterns(self):
        """Setup regex patterns for information extraction"""
        
        # Email pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone patterns (various formats)
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
            r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-123-456-7890
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123 456 7890
        ]
        self.phone_pattern = re.compile('|'.join(phone_patterns))
        
        # LinkedIn pattern
        self.linkedin_pattern = re.compile(
            r'(?:linkedin\.com/in/|linkedin\.com/pub/)([A-Za-z0-9\-_%]+)',
            re.IGNORECASE
        )
        
        # GitHub pattern
        self.github_pattern = re.compile(
            r'(?:github\.com/)([A-Za-z0-9\-_.]+)',
            re.IGNORECASE
        )
        
        # Section headers
        self.section_patterns = {
            'education': re.compile(r'\b(?:education|academic|qualification|degree|university|college)\b', re.IGNORECASE),
            'experience': re.compile(r'\b(?:experience|employment|work|professional|career|job)\b', re.IGNORECASE),
            'skills': re.compile(r'\b(?:skills|technical|technologies|competencies|expertise)\b', re.IGNORECASE),
            'projects': re.compile(r'\b(?:projects|portfolio|work samples)\b', re.IGNORECASE),
            'certifications': re.compile(r'\b(?:certifications|certificates|licenses)\b', re.IGNORECASE),
        }
        
        # Date patterns
        self.date_patterns = [
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b',
            r'\b\d{1,2}/\d{4}\b',
            r'\b\d{4}\b',
            r'\b(?:Present|Current|Now)\b'
        ]
        self.date_pattern = re.compile('|'.join(self.date_patterns), re.IGNORECASE)
        
        # GPA pattern
        self.gpa_pattern = re.compile(r'(?:GPA|Grade|CGPA)[:.]?\s*(\d+\.?\d*)', re.IGNORECASE)
        
        # Degree patterns
        self.degree_patterns = [
            r'\b(?:Bachelor|BS|BA|B\.S\.|B\.A\.)\b',
            r'\b(?:Master|MS|MA|M\.S\.|M\.A\.|MBA)\b',
            r'\b(?:PhD|Ph\.D\.|Doctorate|Ph\.D)\b',
            r'\b(?:Associate|AS|AA|A\.S\.|A\.A\.)\b'
        ]
        self.degree_pattern = re.compile('|'.join(self.degree_patterns), re.IGNORECASE)
    
    def setup_skills_database(self):
        """Setup skills database for extraction"""
        
        # Technical skills categorized
        self.technical_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'go', 'rust',
                'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'bash',
                'powershell', 'sql', 'html', 'css', 'xml', 'json'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask', 'fastapi',
                'spring', 'hibernate', 'struts', 'laravel', 'rails', 'asp.net', 'blazor',
                'xamarin', 'flutter', 'react native', 'ionic', 'cordova'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
                'oracle', 'sql server', 'cassandra', 'dynamodb', 'firebase', 'couchdb'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean', 'linode',
                'vultr', 'cloudflare', 'vercel', 'netlify'
            ],
            'tools': [
                'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'bitbucket',
                'jira', 'confluence', 'slack', 'teams', 'zoom', 'figma', 'sketch',
                'photoshop', 'illustrator', 'indesign'
            ],
            'data_science': [
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
                'matplotlib', 'seaborn', 'plotly', 'jupyter', 'tableau', 'power bi',
                'excel', 'spss', 'sas', 'stata'
            ]
        }
        
        # Flatten all technical skills
        self.all_technical_skills = []
        for category, skills in self.technical_skills.items():
            self.all_technical_skills.extend(skills)
        
        # Soft skills
        self.soft_skills = [
            'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
            'analytical', 'creative', 'detail oriented', 'organized', 'time management',
            'project management', 'agile', 'scrum', 'kanban', 'waterfall'
        ]
        
        # Certifications
        self.certifications = [
            'aws certified', 'azure certified', 'google cloud certified', 'cisco certified',
            'pmp', 'scrum master', 'product owner', 'itil', 'comptia', 'cissp', 'ceh',
            'cisa', 'cism', 'ccna', 'ccnp', 'mcse', 'mcsa', 'rhcsa', 'rhce'
        ]

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        
        text = ""
        
        # Method 1: Try pdfminer for text-based PDFs
        try:
            laparams = LAParams(
                boxes_flow=0.5,
                word_margin=0.1,
                char_margin=2.0,
                line_margin=0.5
            )
            text = extract_text(file_path, laparams=laparams)
            
            # Check if extraction was successful (not just whitespace/noise)
            if len(text.strip()) > 100 and any(c.isalpha() for c in text):
                logger.info("Successfully extracted text using pdfminer")
                return self.clean_extracted_text(text)
                
        except Exception as e:
            logger.warning(f"pdfminer extraction failed: {e}")
        
        # Method 2: OCR fallback for image-based PDFs
        try:
            logger.info("Falling back to OCR extraction")
            text = self.extract_text_with_ocr(file_path)
            if text and len(text.strip()) > 50:
                return self.clean_extracted_text(text)
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            
        # If both methods fail
        if not text or len(text.strip()) < 50:
            raise ValueError("Could not extract meaningful text from PDF")
            
        return self.clean_extracted_text(text)

    def extract_text_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR for image-based PDFs"""
        
        # Convert PDF to images
        try:
            images = pdf2image.convert_from_path(file_path, dpi=300)
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            return ""
        
        full_text = ""
        
        # Process each page
        for i, image in enumerate(images):
            try:
                # Configure tesseract for better results
                custom_config = r'--oem 3 --psm 6 -l eng'
                page_text = pytesseract.image_to_string(image, config=custom_config)
                full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
                
            except Exception as e:
                logger.warning(f"OCR failed for page {i+1}: {e}")
                continue
                
        return full_text

    def clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\t+', ' ', text)
        text = re.sub(r' +', ' ', text)
        
        # Fix common OCR/extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)  # Add space before numbers
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)  # Add space after numbers
        
        # Fix hyphenation issues
        text = re.sub(r'-\s*\n\s*', '', text)  # Remove hyphenation at line breaks
        
        # Remove header/footer patterns (common resume artifacts)
        header_footer_patterns = [
            r'Page \d+ of \d+',
            r'\d+/\d+',
            r'Resume of .+',
            r'.+\s+Resume',
            r'Confidential',
            r'DRAFT',
        ]
        
        for pattern in header_footer_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        return text.strip()

    async def parse_resume(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Main method to parse resume and extract structured information"""
        
        try:
            # Extract text from PDF
            raw_text = self.extract_text_from_pdf(file_path)
            logger.info(f"Extracted {len(raw_text)} characters from {filename}")
            
            # Parse sections
            sections = self.identify_sections(raw_text)
            logger.info(f"Identified sections: {list(sections.keys())}")
            
            # Extract structured information
            contact_info = self.extract_contact_info(raw_text)
            education = self.extract_education(sections.get('education', []), raw_text)
            experience = self.extract_experience(sections.get('experience', []), raw_text)
            skills = self.extract_skills(sections.get('skills', []), raw_text)
            projects = self.extract_projects(sections.get('projects', []), raw_text)
            
            # Compile results
            parsed_data = {
                'contact_info': contact_info,
                'education': education,
                'experience': experience,
                'skills': skills,
                'projects': projects,
                'sections': sections,
                'raw_text': raw_text,
                'filename': filename
            }
            
            logger.info(f"Successfully parsed resume: {contact_info.get('name', 'Unknown')}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume {filename}: {str(e)}")
            raise

    def identify_sections(self, text: str) -> Dict[str, List[str]]:
        """Identify and extract resume sections"""
        
        sections = {}
        lines = text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            section_found = None
            for section_name, pattern in self.section_patterns.items():
                if pattern.search(line) and len(line) < 50:  # Likely a header
                    section_found = section_name
                    break
            
            if section_found:
                # Save previous section
                if current_section and section_content:
                    sections[current_section] = section_content
                
                # Start new section
                current_section = section_found
                section_content = []
            else:
                # Add content to current section
                if current_section:
                    section_content.append(line)
                    
        # Save last section
        if current_section and section_content:
            sections[current_section] = section_content
            
        return sections

    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information from resume text"""
        
        contact_info = {
            'name': None,
            'email': None,
            'phone': None,
            'location': None,
            'linkedin': None,
            'github': None
        }
        
        # Extract email
        email_match = self.email_pattern.search(text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Extract phone
        phone_match = self.phone_pattern.search(text)
        if phone_match:
            contact_info['phone'] = phone_match.group().strip()
        
        # Extract LinkedIn
        linkedin_match = self.linkedin_pattern.search(text)
        if linkedin_match:
            contact_info['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
        
        # Extract GitHub
        github_match = self.github_pattern.search(text)
        if github_match:
            contact_info['github'] = f"github.com/{github_match.group(1)}"
        
        # Extract name (heuristic: first line or near email)
        lines = text.split('\n')
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            line = line.strip()
            if line and not any(char in line for char in ['@', 'http', '(', ')']):
                # Likely a name if it's 2-4 words, each capitalized
                words = line.split()
                if 2 <= len(words) <= 4 and all(word[0].isupper() for word in words if word):
                    contact_info['name'] = line
                    break
        
        # Extract location (heuristic: city, state pattern)
        location_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2}(?:\s+\d{5})?)', re.IGNORECASE)
        location_match = location_pattern.search(text)
        if location_match:
            contact_info['location'] = location_match.group().strip()
        
        return contact_info

    def extract_education(self, education_lines: List[str], full_text: str) -> List[Dict[str, Any]]:
        """Extract education information"""
        
        education_entries = []
        
        if not education_lines:
            # Try to find education info in full text
            education_lines = []
            lines = full_text.split('\n')
            in_education_section = False
            
            for line in lines:
                if self.section_patterns['education'].search(line):
                    in_education_section = True
                    continue
                elif any(pattern.search(line) for pattern in self.section_patterns.values() if pattern != self.section_patterns['education']):
                    in_education_section = False
                elif in_education_section:
                    education_lines.append(line)
        
        # Parse education entries
        current_entry = {}
        
        for line in education_lines:
            line = line.strip()
            if not line:
                if current_entry:
                    education_entries.append(current_entry)
                    current_entry = {}
                continue
            
            # Check for degree
            degree_match = self.degree_pattern.search(line)
            if degree_match:
                current_entry['degree'] = degree_match.group().strip()
            
            # Check for GPA
            gpa_match = self.gpa_pattern.search(line)
            if gpa_match:
                current_entry['gpa'] = gpa_match.group(1)
            
            # Check for dates
            dates = self.date_pattern.findall(line)
            if dates:
                if len(dates) >= 2:
                    current_entry['start_date'] = dates[0]
                    current_entry['end_date'] = dates[1]
                elif len(dates) == 1:
                    current_entry['end_date'] = dates[0]
            
            # Institution name (heuristic: line with university/college keywords)
            if any(keyword in line.lower() for keyword in ['university', 'college', 'institute', 'school']):
                current_entry['institution'] = line.strip()
            
            # Field of study (if not already captured)
            if 'degree' not in current_entry and any(field in line.lower() for field in ['computer science', 'engineering', 'business', 'arts', 'science']):
                current_entry['field_of_study'] = line.strip()
        
        # Add last entry
        if current_entry:
            education_entries.append(current_entry)
        
        return education_entries

    def extract_experience(self, experience_lines: List[str], full_text: str) -> List[Dict[str, Any]]:
        """Extract work experience information"""
        
        experience_entries = []
        
        if not experience_lines:
            # Try to find experience info in full text
            experience_lines = []
            lines = full_text.split('\n')
            in_experience_section = False
            
            for line in lines:
                if self.section_patterns['experience'].search(line):
                    in_experience_section = True
                    continue
                elif any(pattern.search(line) for pattern in self.section_patterns.values() if pattern != self.section_patterns['experience']):
                    in_experience_section = False
                elif in_experience_section:
                    experience_lines.append(line)
        
        # Parse experience entries
        current_entry = {}
        current_details = []
        
        for line in experience_lines:
            line = line.strip()
            
            if not line:
                if current_entry:
                    if current_details:
                        current_entry['details'] = current_details
                    experience_entries.append(current_entry)
                    current_entry = {}
                    current_details = []
                continue
            
            # Check if line starts with bullet point
            if line.startswith(('•', '-', '*', '◦')):
                current_details.append(line[1:].strip())
                continue
            
            # Check for dates
            dates = self.date_pattern.findall(line)
            if dates:
                if len(dates) >= 2:
                    current_entry['start_date'] = dates[0]
                    current_entry['end_date'] = dates[1]
                elif len(dates) == 1:
                    current_entry['end_date'] = dates[0]
            
            # Job title and company (heuristic: title then company pattern)
            if not current_entry.get('title') and not any(char.isdigit() for char in line):
                # Likely a job title
                current_entry['title'] = line
            elif not current_entry.get('company') and not any(char.isdigit() for char in line):
                # Likely a company name
                current_entry['company'] = line
        
        # Add last entry
        if current_entry:
            if current_details:
                current_entry['details'] = current_details
            experience_entries.append(current_entry)
        
        return experience_entries

    def extract_skills(self, skills_lines: List[str], full_text: str) -> Dict[str, List[str]]:
        """Extract skills information"""
        
        skills = {
            'technical': [],
            'soft': [],
            'languages': [],
            'certifications': []
        }
        
        # Combine skills section and full text for analysis
        text_to_analyze = ' '.join(skills_lines) + ' ' + full_text
        text_lower = text_to_analyze.lower()
        
        # Extract technical skills
        for skill in self.all_technical_skills:
            if skill.lower() in text_lower:
                if skill.lower() not in [s.lower() for s in skills['technical']]:
                    skills['technical'].append(skill)
        
        # Extract soft skills
        for skill in self.soft_skills:
            if skill.lower() in text_lower:
                if skill.lower() not in [s.lower() for s in skills['soft']]:
                    skills['soft'].append(skill)
        
        # Extract certifications
        for cert in self.certifications:
            if cert.lower() in text_lower:
                if cert.lower() not in [s.lower() for s in skills['certifications']]:
                    skills['certifications'].append(cert)
        
        # Extract programming languages (more comprehensive)
        programming_languages = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab'
        ]
        
        for lang in programming_languages:
            if lang.lower() in text_lower:
                if lang.lower() not in [s.lower() for s in skills['technical']]:
                    skills['technical'].append(lang)
        
        return skills

    def extract_projects(self, projects_lines: List[str], full_text: str) -> List[Dict[str, Any]]:
        """Extract project information"""
        
        projects = []
        
        if not projects_lines:
            return projects
        
        current_project = {}
        current_details = []
        
        for line in projects_lines:
            line = line.strip()
            
            if not line:
                if current_project:
                    if current_details:
                        current_project['description'] = ' '.join(current_details)
                    projects.append(current_project)
                    current_project = {}
                    current_details = []
                continue
            
            # Check if line starts with bullet point
            if line.startswith(('•', '-', '*', '◦')):
                current_details.append(line[1:].strip())
                continue
            
            # Project name (first non-bullet line)
            if not current_project.get('name'):
                current_project['name'] = line
            else:
                current_details.append(line)
        
        # Add last project
        if current_project:
            if current_details:
                current_project['description'] = ' '.join(current_details)
            projects.append(current_project)
        
        return projects