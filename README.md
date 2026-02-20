# AI Resume Analyzer and Job Recommendation System

A comprehensive full-stack application that uses AI and machine learning to analyze resumes, match candidates with jobs, and provide personalized recommendations.

## Features

### Candidate Side
- **Resume Upload & Analysis**: Upload resumes (PDF, DOCX, images) with AI-powered text extraction and skill analysis
- **Job Recommendations**: Get personalized job recommendations based on resume analysis with match percentages
- **Skill Gap Analysis**: Identify missing skills and get upskilling suggestions
- **Application Tracking**: Track job applications and their status
- **Interactive Dashboard**: Comprehensive overview of job search activity

### HR/Recruiter Side
- **Job Posting**: Create and manage job postings with skill requirements
- **Candidate Ranking**: AI-powered candidate ranking based on job requirements
- **Application Management**: Review and manage applications with status tracking
- **Email Notifications**: Automated email notifications for new applications
- **Analytics Dashboard**: Track recruitment metrics and application statistics

## Tech Stack

### Backend
- **Django** with Django REST Framework
- **PostgreSQL** database
- **Python** with ML libraries (scikit-learn, nltk, spacy)
- **Email** functionality with Django SMTP backend

### Frontend
- **React** with Vite
- **Ant Design** UI components
- **React Query** for data fetching
- **React Router** for navigation
- **Axios** for API calls

### ML/NLP
- **TF-IDF Vectorization** for text processing
- **Cosine Similarity** for matching algorithms
- **NLP** for skill extraction and text analysis
- **OCR** for image processing

## Project Structure

```
new_project/
├── resume_analyzer/          # Django project settings
├── accounts/                 # User management app
├── resumes/                  # Resume processing app
├── jobs/                     # Job management app
├── applications/             # Application tracking app
├── ml_engine/               # ML algorithms app
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   └── services/       # API services
├── manage.py                # Django management script
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Database Models

### Core Models
- **User**: Extended user model with role (candidate/HR)
- **Resume**: Resume storage with extracted data
- **Job**: Job postings with requirements
- **Application**: Job applications with tracking
- **SkillProfile**: User skill profiles

### ML Models
- **JobMatch**: Resume-job matching results
- **UpskillingSuggestion**: Learning recommendations
- **MLModel**: Trained model metadata

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis (optional, for caching)

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd new_project
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your database and email settings
```

5. **Setup PostgreSQL database**
```sql
CREATE DATABASE resume_analyzer_db;
CREATE USER resume_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE resume_analyzer_db TO resume_user;
```

6. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create superuser**
```bash
python manage.py createsuperuser
```

8. **Download NLP models**
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
python -c "import spacy; spacy.cli.download('en_core_web_sm')"
```

9. **Start Django server**
```bash
python manage.py runserver
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env if needed
```

4. **Start React development server**
```bash
npm start
```

## Usage

### For Candidates
1. Register as a candidate
2. Upload your resume (PDF, DOCX, or image)
3. Wait for AI processing (usually takes 30-60 seconds)
4. View your resume analysis and skill extraction
5. Get personalized job recommendations
6. Apply to jobs with one click
7. Track your applications and get skill gap suggestions

### For HR/Recruiters
1. Register as an HR user
2. Post new job openings with detailed requirements
3. View ranked candidates for your jobs
4. Review applications with AI-powered match scores
5. Change application status and add notes
6. Get email notifications for new applications
7. Track recruitment metrics

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/me/` - Get current user

### Resumes
- `POST /api/resumes/upload/` - Upload resume
- `GET /api/resumes/` - List user resumes
- `GET /api/resumes/{id}/` - Get resume details
- `GET /api/resumes/{id}/analysis/` - Get resume analysis

### Jobs
- `GET /api/jobs/` - List jobs
- `POST /api/jobs/create/` - Create job (HR only)
- `GET /api/jobs/recommendations/` - Get job recommendations
- `POST /api/jobs/{id}/rank-candidates/` - Rank candidates (HR only)

### Applications
- `POST /api/applications/create/` - Apply to job
- `GET /api/applications/` - List applications
- `POST /api/applications/{id}/status/` - Change status (HR only)

### ML Engine
- `POST /api/ml/extract-skills/` - Extract skills from text
- `POST /api/ml/calculate-match/` - Calculate job match
- `GET /api/ml/recommendations/` - Get recommendations
- `GET /api/ml/upskilling/` - Get upskilling suggestions

## ML Pipeline

### Resume Processing
1. **Text Extraction**: Uses pdfplumber, python-docx, and OCR for images
2. **NLP Processing**: Tokenization, stopword removal, lemmatization
3. **Skill Extraction**: Pattern matching and NLP-based extraction
4. **Feature Vectorization**: TF-IDF vector creation
5. **Analysis**: Completeness, skills, experience, and education scoring

### Job Matching
1. **Vector Similarity**: Cosine similarity between resume and job vectors
2. **Skills Matching**: Direct skill comparison with confidence scoring
3. **Experience Matching**: Level and duration analysis
4. **Education Matching**: Degree and field comparison
5. **Overall Scoring**: Weighted combination of all factors

### Recommendations
1. **Collaborative Filtering**: Based on similar candidates
2. **Content-Based Filtering**: Based on skills and experience
3. **Diversity Selection**: Ensures variety in recommendations
4. **Skill Gap Analysis**: Identifies learning opportunities

## Email Configuration

Configure email settings in `.env`:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=no-reply@yourcompany.com
```

For Gmail, enable "Less secure apps" or use an App Password.

## Deployment

### Backend (Django)
1. Set `DEBUG=False` in production
2. Configure `ALLOWED_HOSTS`
3. Use environment variables for sensitive data
4. Set up PostgreSQL in production
5. Configure static files serving
6. Use Gunicorn or uWSGI as WSGI server

### Frontend (React)
1. Build the project: `npm run build`
2. Serve static files with Nginx or similar
3. Configure API URL for production
4. Enable HTTPS in production

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed description
4. Include error messages and steps to reproduce

## Future Enhancements

- [ ] Real-time notifications with WebSockets
- [ ] Video interview integration
- [ ] Advanced analytics dashboard
- [ ] Mobile app development
- [ ] Integration with LinkedIn and other job platforms
- [ ] Automated interview scheduling
- [ ] Reference checking system
- [ ] Salary negotiation assistant
