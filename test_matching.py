#!/usr/bin/env python
"""
Test script to verify job-resume matching functionality
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')
django.setup()

from django.contrib.auth import get_user_model
from resumes.models import Resume
from jobs.models import Job, JobMatch
from jobs.recommendation_engine import recommendation_engine

User = get_user_model()

def test_job_matching():
    print("=== Job-Resume Matching Test ===\n")
    
    # Check for processed resumes
    resumes = Resume.objects.filter(processing_status='completed')
    print(f"Found {resumes.count()} processed resumes:")
    
    for resume in resumes:
        print(f"  - {resume.title} (User: {resume.user.username})")
        print(f"    Skills: {resume.extracted_skills}")
        print()
    
    # Check for active jobs
    jobs = Job.objects.filter(is_active=True)
    print(f"Found {jobs.count()} active jobs:")
    
    for job in jobs:
        print(f"  - {job.title} at {job.company}")
        print(f"    Required Skills: {job.required_skills}")
        print(f"    Preferred Skills: {job.preferred_skills}")
        print()
    
    # Test matching for each user with a resume
    for resume in resumes:
        print(f"\n=== Matching for {resume.user.username} ===")
        
        # Get recommendations
        recommendations = recommendation_engine.get_user_recommendations(
            user=resume.user,
            limit=5,
            min_score=10.0  # Lower threshold for testing
        )
        
        print(f"Found {len(recommendations)} recommendations:")
        
        for rec in recommendations:
            print(f"\n  Job: {rec['job'].title} at {rec['job'].company}")
            print(f"  Match Score: {rec['match_percentage']:.1f}%")
            print(f"  Matched Skills: {rec['matched_skills']}")
            print(f"  Missing Skills: {rec['missing_skills']}")
            print(f"  Reason: {rec['reason']}")
        
        # Check JobMatch records
        matches = JobMatch.objects.filter(resume=resume).select_related('job')
        print(f"\n  Total JobMatch records: {matches.count()}")
        for match in matches:
            print(f"    - {match.job.title}: {match.overall_score:.1f}%")

if __name__ == "__main__":
    test_job_matching()
