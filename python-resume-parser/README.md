# Python Resume Parser + ATS Scoring + Recruiter Dashboard

A complete Python-based Resume Parsing & ATS Scoring System with a Recruiter Dashboard, inspired by open-resume but fully reimplemented in Python with enhanced features.

## 🚀 Features

### Backend (FastAPI)
- **Resume Parsing**: Extract structured data from PDF resumes
- **ATS Scoring**: Compute similarity between resume and job description using TF-IDF and optional SBERT
- **Improvement Suggestions**: AI-powered resume enhancement recommendations
- **RESTful API**: Complete API for all operations

### Resume Parsing Pipeline
- **Multi-format Support**: Text-based PDFs with OCR fallback
- **Text Cleaning**: Advanced preprocessing (hyphenation fix, header/footer removal)
- **Field Extraction**: Name, email, phone, skills, experience, education
- **Smart Parsing**: Section detection and content structuring

### ATS Scoring System
- **TF-IDF Vectorization**: Industry-standard text similarity
- **Cosine Similarity**: Overall match scoring
- **Section-based Scoring**: Granular analysis (skills, experience, education)
- **Keyword Analysis**: Matched and missing keywords identification

### Recruiter Dashboard (Streamlit)
- **Interactive UI**: Upload resumes and job descriptions
- **Visual Analytics**: Score breakdowns, charts, and insights
- **Candidate Management**: Track and compare candidates
- **Suggestions Engine**: Actionable resume improvement tips

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │   ML Models     │
│   Dashboard     │◄──►│    Backend      │◄──►│   & Pipeline    │
│                 │    │                 │    │                 │
│ • Upload UI     │    │ • REST API      │    │ • PDF Parser    │
│ • Analytics     │    │ • Resume Parser │    │ • TF-IDF        │
│ • Scoring View  │    │ • ATS Scorer    │    │ • SBERT         │
│ • Suggestions   │    │ • Database      │    │ • NLP Pipeline  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Project Structure

```
python-resume-parser/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Core functionality
│   │   ├── models/            # Data models
│   │   └── services/          # Business logic
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/                  # Streamlit Dashboard
│   ├── app.py                 # Main dashboard app
│   ├── pages/                 # Dashboard pages
│   ├── components/            # Reusable components
│   ├── requirements.txt
│   └── Dockerfile
├── models/                    # ML models and embeddings
├── data/                      # Sample data
│   ├── resumes/              # Sample PDF resumes
│   └── job_descriptions/      # Sample JDs
├── tests/                     # Test suite
├── scripts/                   # Utility scripts
├── docker-compose.yml
└── README.md
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: Streamlit
- **ML/NLP**: scikit-learn, sentence-transformers, spaCy, NLTK
- **PDF Processing**: pdfminer.six, pdf2image, pytesseract
- **Database**: SQLite (development), PostgreSQL (production)
- **Deployment**: Docker, Docker Compose

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose (optional)

### Method 1: Docker Compose (Recommended)

```bash
git clone <your-repo>
cd python-resume-parser
docker-compose up --build
```

- Backend API: http://localhost:8000
- Dashboard: http://localhost:8501
- API Documentation: http://localhost:8000/docs

### Method 2: Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Dashboard (new terminal)
cd dashboard
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

## 📖 API Documentation

### Resume Processing

```http
POST /parse_resume
Content-Type: multipart/form-data

Response:
{
  "id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-234-567-8900",
  "skills": ["Python", "Machine Learning"],
  "experience": [...],
  "education": [...],
  "raw_text": "..."
}
```

### ATS Scoring

```http
POST /score_resume
Content-Type: application/json

{
  "resume_id": "uuid",
  "job_description": "Software engineer role requiring Python..."
}

Response:
{
  "overall_score": 0.75,
  "section_scores": {
    "skills": 0.8,
    "experience": 0.7,
    "education": 0.6
  },
  "matched_keywords": ["python", "machine learning"],
  "missing_keywords": ["aws", "docker"]
}
```

## 🧪 Sample Data

The project includes:
- **3 Sample Resumes**: Various formats and experience levels
- **2 Job Descriptions**: Software engineering roles
- **Expected Outputs**: Score examples and suggestions

## 🔬 Testing

```bash
cd backend
pytest tests/ -v
```

## 📊 Dashboard Features

### Pages:
1. **Upload Resume**: Drag-and-drop PDF upload
2. **Upload Job Description**: Text input for JD
3. **Parsed Resume Viewer**: Structured display of extracted data
4. **ATS Score Breakdown**: Visual scoring with charts
5. **Suggestions**: Improvement recommendations
6. **Candidate List**: Track multiple candidates
7. **Analytics**: Aggregate insights and trends

### Charts & Visualizations:
- Score distribution histograms
- Keyword match/miss analysis
- Skills gap identification
- Candidate comparison radar charts

## 🎯 Use Cases

### For Recruiters:
- Quickly screen large volumes of resumes
- Identify skill gaps and requirements match
- Generate standardized candidate assessments
- Track recruitment pipeline analytics

### For Job Seekers:
- Optimize resume for specific job descriptions
- Identify missing skills and keywords
- Get actionable improvement suggestions
- Understand ATS compatibility

### For HR Teams:
- Standardize resume evaluation process
- Generate hiring insights and reports
- Improve job description effectiveness
- Track recruitment metrics

## 🔧 Configuration

### Environment Variables:
```bash
# Backend
DATABASE_URL=sqlite:///./resumes.db
SECRET_KEY=your-secret-key
DEBUG=true

# Dashboard
BACKEND_URL=http://localhost:8000
```

### Customization:
- **Skills Dictionary**: Modify `backend/app/core/skills.py`
- **Scoring Weights**: Adjust in `backend/app/core/scoring.py`
- **UI Theme**: Update `dashboard/components/theme.py`

## 🚀 Deployment

### Production Deployment:
```bash
# Update docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to cloud platforms:
# - AWS ECS/Fargate
# - Google Cloud Run
# - Azure Container Instances
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Interview Questions & Answers

### Technical Architecture

**Q: How does the resume parsing pipeline work?**
A: The pipeline has 4 main stages:
1. **PDF Text Extraction**: Uses pdfminer.six for text-based PDFs, with OCR fallback using pytesseract
2. **Text Preprocessing**: Cleans text by fixing hyphenation, removing headers/footers, normalizing spacing
3. **Section Detection**: Uses NLP techniques and regex patterns to identify resume sections
4. **Field Extraction**: Applies specific extractors for name, email, phone, skills, experience, and education

**Q: Explain the ATS scoring algorithm.**
A: The scoring uses multiple approaches:
- **TF-IDF Vectorization**: Converts text to numerical vectors representing term importance
- **Cosine Similarity**: Measures angle between resume and JD vectors (0-1 score)
- **Section-wise Scoring**: Separate scores for skills, experience, education
- **Keyword Matching**: Identifies present and missing keywords for targeted feedback

**Q: How do you handle different resume formats?**
A: Multi-layered approach:
- **Text-based PDFs**: Direct extraction with pdfminer.six
- **Image-based PDFs**: OCR with pytesseract after converting to images
- **Text Cleaning**: Robust preprocessing handles various formatting inconsistencies
- **Section Detection**: Flexible patterns accommodate different resume structures

### System Design

**Q: How would you scale this system?**
A: Several strategies:
- **Microservices**: Split parsing, scoring, and dashboard into separate services
- **Async Processing**: Use Celery/Redis for background resume processing
- **Caching**: Redis for frequently accessed data and computed scores
- **Load Balancing**: Multiple API instances behind nginx
- **Database**: Migrate to PostgreSQL with read replicas

**Q: What about security and privacy?**
A: Multiple layers:
- **Data Encryption**: Encrypt sensitive resume data at rest and in transit
- **Access Control**: JWT tokens and role-based permissions
- **Data Retention**: Configurable resume deletion policies
- **Audit Logging**: Track all data access and modifications
- **Compliance**: GDPR/CCPA compliance features

### Machine Learning

**Q: How do you improve accuracy over time?**
A: Continuous improvement approach:
- **Feedback Loop**: Collect recruiter feedback on parsing accuracy
- **Active Learning**: Retrain models with corrected examples
- **A/B Testing**: Test different scoring algorithms
- **Domain Adaptation**: Fine-tune models for specific industries
- **Regular Evaluation**: Monitor performance metrics and update models

**Q: What about bias in the scoring system?**
A: Bias mitigation strategies:
- **Fairness Metrics**: Monitor scoring across demographic groups
- **Bias Testing**: Regular audits with diverse resume sets
- **Transparent Scoring**: Clear explanation of score components
- **Configurable Weights**: Allow organizations to adjust scoring criteria
- **Human Oversight**: Recommendations include human review requirements

## 📈 Future Enhancements

- **Multi-language Support**: Extend parsing to non-English resumes
- **Video Resume Analysis**: Add support for video resume parsing
- **Integration APIs**: Connect with ATS systems (Greenhouse, Workday)
- **Mobile App**: Native mobile application for recruiters
- **Advanced ML**: Implement transformer-based models for better understanding