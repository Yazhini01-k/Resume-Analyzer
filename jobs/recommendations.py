"""
Strict Resume-Based Job Recommendation System

This module provides job recommendations based ONLY on uploaded resume skills.
No hardcoded candidate data, static profiles, or fallback logic.
"""

from django.db.models import Q, Count, Prefetch
from django.contrib.auth import get_user_model
from .models import Job, JobSkillRequirement
from resumes.models import Resume, SkillProfile

User = get_user_model()


def recommend_jobs(user):
    """
    STRICT: Recommend jobs based ONLY on the user's uploaded resume skills.
    
    Args:
        user: The user object (jobseeker)
    
    Returns:
        dict: Contains either recommended jobs or appropriate message
    """
    
    # 1. Check if user has uploaded a resume
    try:
        latest_resume = Resume.objects.filter(
            user=user, 
            processing_status='completed'
        ).select_related('user').order_by('-created_at').first()
        
        if not latest_resume:
            return {
                'message': 'Please upload your resume to see job recommendations.',
                'status': 'no_resume'
            }
        
        # 2. Get user's skill profile
        try:
            skill_profile = SkillProfile.objects.get(user=user)
            user_skills = skill_profile.skills or {}
            
            if not user_skills:
                return {
                    'message': 'No skills found in your resume. Please ensure your resume contains skill information.',
                    'status': 'no_skills'
                }
                
        except SkillProfile.DoesNotExist:
            return {
                'message': 'No skill profile found. Please upload and process your resume first.',
                'status': 'no_skill_profile'
            }
        
        # 3. Get only active jobs with optimized queries
        active_jobs = Job.objects.filter(
            is_active=True
        ).select_related(
            'posted_by'
        ).prefetch_related(
            Prefetch(
                'skill_requirements',
                queryset=JobSkillRequirement.objects.select_related('skill')
            )
        )
        
        if not active_jobs.exists():
            return {
                'message': 'No active jobs available at the moment.',
                'status': 'no_jobs'
            }
        
        # 4. Calculate match percentage for each job
        job_matches = []
        user_skill_names = set(user_skills.keys())
        
        for job in active_jobs:
            # Get job skill requirements
            job_skill_requirements = job.skill_requirements.all()
            
            if not job_skill_requirements:
                continue  # Skip jobs with no skill requirements
            
            # Extract job skill names
            job_skill_names = set()
            for req in job_skill_requirements:
                job_skill_names.add(req.skill.name.lower())
            
            # Calculate overlapping skills
            matching_skills = user_skill_names.intersection(job_skill_names)
            
            # Only include jobs where at least 1 skill matches
            if len(matching_skills) == 0:
                continue
            
            # Calculate match percentage
            match_percentage = (len(matching_skills) / len(job_skill_names)) * 100
            
            job_matches.append({
                'job': job,
                'match_percentage': round(match_percentage, 2),
                'matching_skills': list(matching_skills),
                'total_required_skills': len(job_skill_names),
                'matched_skills_count': len(matching_skills)
            })
        
        # 5. Sort by highest match percentage
        job_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # 6. Return top 10 matched jobs
        top_matches = job_matches[:10]
        
        if not top_matches:
            return {
                'message': 'No matching jobs found based on your resume.',
                'status': 'no_matches'
            }
        
        # Format the response
        recommended_jobs = []
        for match in top_matches:
            job = match['job']
            recommended_jobs.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description[:200] + '...' if len(job.description) > 200 else job.description,
                'job_type': job.job_type,
                'experience_level': job.experience_level,
                'salary_range': job.salary_range,
                'posted_date': job.created_at.strftime('%Y-%m-%d'),
                'match_percentage': match['match_percentage'],
                'matching_skills': match['matching_skills'],
                'total_required_skills': match['total_required_skills'],
                'matched_skills_count': match['matched_skills_count']
            })
        
        return {
            'recommended_jobs': recommended_jobs,
            'total_matches': len(job_matches),
            'status': 'success',
            'user_skills_count': len(user_skills),
            'resume_title': latest_resume.title
        }
        
    except Exception as e:
        return {
            'message': f'An error occurred while generating recommendations: {str(e)}',
            'status': 'error'
        }


def get_user_skill_summary(user):
    """
    Get a summary of user's skills from their resume.
    
    Args:
        user: The user object
    
    Returns:
        dict: User skill summary or error message
    """
    try:
        skill_profile = SkillProfile.objects.get(user=user)
        skills = skill_profile.skills or {}
        
        if not skills:
            return {
                'message': 'No skills found in your resume.',
                'status': 'no_skills'
            }
        
        return {
            'skills': skills,
            'total_skills': len(skills),
            'status': 'success'
        }
        
    except SkillProfile.DoesNotExist:
        return {
            'message': 'No skill profile found. Please upload and process your resume first.',
            'status': 'no_skill_profile'
        }
    except Exception as e:
        return {
            'message': f'Error retrieving skills: {str(e)}',
            'status': 'error'
        }
