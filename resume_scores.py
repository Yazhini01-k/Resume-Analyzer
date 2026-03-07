import os
import sys

# Add project directory to Python path
project_dir = r"c:\Users\yazhi\OneDrive\yazhu\2026 final year project\new job recommandation_page\Resume-Analyzer"
sys.path.insert(0, project_dir)
sys.path.insert(0, os.path.join(project_dir, 'venv', 'Lib', 'site-packages'))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')

import django
django.setup()

from ml_engine.ml_algorithms import JobMatcher
from jobs.models import Job
from resumes.models import Resume

print('🎯 Resume-Job Matching Scores')
print('=' * 40)

matcher = JobMatcher()
jobs = list(Job.objects.all())
resumes = list(Resume.objects.all())

for resume in resumes:
    print(f'\n📄 {resume.title}')
    print(f'   Skills: {len(resume.extracted_skills or [])}')
    
    resume_data = {
        'skills': resume.extracted_skills or [],
        'experience': resume.extracted_experience or [],
        'education': resume.extracted_education or [],
        'processed_text': resume.processed_text or ''
    }
    
    for job in jobs:
        job_data = {
            'required_skills': job.required_skills or [],
            'preferred_skills': job.preferred_skills or [],
            'experience_level': job.experience_level or 'mid',
            'education_requirements': [],
            'description': job.description or '',
            'requirements': job.requirements or ''
        }
        
        result = matcher.calculate_comprehensive_match(resume_data, job_data)
        print(f'   {job.title}: {result["overall_score"]:.1f}% (Exp: {result["has_experience"]})')

input('\nPress Enter...')
