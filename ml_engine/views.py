from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast
from .models import (
    MLModel, SkillExtractionResult, JobMatchResult, RecommendationLog,
    # UpskillingSuggestion, ModelTrainingLog  # Temporarily disabled
    ModelTrainingLog
)
from .serializers import (
    MLModelSerializer, SkillExtractionResultSerializer, JobMatchResultSerializer,
    RecommendationLogSerializer, ModelTrainingLogSerializer,
    # UpskillingSuggestionSerializer  # Temporarily disabled
)
from .ml_algorithms import SkillExtractor, JobMatcher, RecommendationEngine
from resumes.models import Resume
from jobs.models import Job, JobSkillRequirement
from applications.models import Application
from accounts.models import User


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def extract_skills(request):
    """Extract skills from resume text"""
    text = request.data.get('text', '')
    resume_id = request.data.get('resume_id', None)
    
    if not text:
        return Response(
            {'error': 'Text is required for skill extraction'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Initialize skill extractor
    extractor = SkillExtractor()
    
    # Extract skills
    result = extractor.extract_skills(text)
    
    # Save result if resume_id is provided
    if resume_id:
        try:
            resume = Resume.objects.get(id=resume_id, user=request.user)
            SkillExtractionResult.objects.create(
                resume=resume,
                extracted_skills=result['extracted_skills'],
                confidence_scores=result['confidence_scores'],
                processing_time_ms=result['processing_time_ms'],
                model_version='v1.0'
            )
        except Resume.DoesNotExist:
            pass  # Don't fail if resume doesn't exist
    
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def calculate_job_match(request):
    """Calculate job match score"""
    resume_id = request.data.get('resume_id')
    job_id = request.data.get('job_id')
    
    if not resume_id or not job_id:
        return Response(
            {'error': 'Both resume_id and job_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get resume and job
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    job = get_object_or_404(Job, id=job_id)
    
    # Prepare data for matching
    resume_data = {
        'skills': resume.extracted_skills or [],
        'experience': resume.extracted_experience or [],
        'education': resume.extracted_education or [],
        'processed_text': resume.processed_text or ''
    }
    
    job_data = {
        'required_skills': job.required_skills or [],
        'preferred_skills': job.preferred_skills or [],
        'experience_level': job.experience_level,
        'education_requirements': [],  # Could be extracted from job description
        'description': job.description,
        'requirements': job.requirements or ''
    }
    
    # Calculate match
    matcher = JobMatcher()
    match_result = matcher.calculate_comprehensive_match(resume_data, job_data)
    
    # Save result
    JobMatchResult.objects.update_or_create(
        resume=resume,
        job=job,
        defaults={
            'overall_score': match_result['overall_score'],
            'skills_score': match_result['skills_score'],
            'experience_score': match_result['experience_score'],
            'education_score': match_result['education_score'],
            'matched_skills': match_result['matched_skills'],
            'missing_skills': match_result['missing_skills'],
            'skill_gap_analysis': match_result['skill_gap_analysis'],
            'processing_time_ms': match_result['processing_time_ms'],
            'algorithm_version': 'v1.0'
        }
    )
    
    return Response(match_result)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_recommendations(request):
    """Get personalized recommendations"""
    user = request.user
    
    # Get user's latest resume
    latest_resume = Resume.objects.filter(
        user=user, 
        processing_status='completed'
    ).order_by('-created_at').first()
    
    if not latest_resume:
        return Response(
            {'error': 'No processed resume found'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get recommendation type
    recommendation_type = request.query_params.get('type', 'jobs')
    
    if recommendation_type == 'jobs':
        return _get_job_recommendations(request, latest_resume)
    elif recommendation_type == 'skills':
        return _get_skill_recommendations(request, latest_resume)
    else:
        return Response(
            {'error': 'Invalid recommendation type'},
            status=status.HTTP_400_BAD_REQUEST
        )


def _get_job_recommendations(request, resume):
    """Get job recommendations"""
    user = request.user
    
    # Prepare resume data
    resume_data = {
        'skills': resume.extracted_skills or [],
        'experience': resume.extracted_experience or [],
        'education': resume.extracted_education or [],
        'processed_text': resume.processed_text or ''
    }
    
    # Get all active jobs
    active_jobs = Job.objects.filter(is_active=True)
    
    # Convert jobs to dict format
    jobs_data = []
    for job in active_jobs:
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'description': job.description,
            'requirements': job.requirements or '',
            'required_skills': job.required_skills or [],
            'preferred_skills': job.preferred_skills or [],
            'experience_level': job.experience_level,
            'job_type': job.job_type,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'posted_date': job.posted_date.isoformat() if job.posted_date else None,
            'is_remote': job.is_remote
        })
    
    # Get recommendations
    engine = RecommendationEngine()
    recommendations = engine.get_job_recommendations(resume_data, jobs_data)
    
    # Log recommendation
    RecommendationLog.objects.create(
        user=user,
        resume=resume,
        recommendation_type='jobs',
        recommendations=[rec['job']['id'] for rec in recommendations]
    )
    
    return Response({
        'recommendations': recommendations,
        'total_count': len(recommendations)
    })


def _get_skill_recommendations(request, resume):
    """Get upskilling recommendations"""
    user = request.user
    
    # Get user's skills
    user_skills = resume.extracted_skills or []
    
    # Get jobs user is interested in (based on applications or views)
    applied_jobs = Job.objects.filter(
        applications__candidate=user
    ).distinct()
    
    # Convert to dict format
    target_jobs = []
    for job in applied_jobs:
        target_jobs.append({
            'id': job.id,
            'title': job.title,
            'required_skills': job.required_skills or []
        })
    
    # If no applied jobs, get top matching jobs
    if not target_jobs:
        top_jobs = Job.objects.filter(is_active=True)[:10]
        for job in top_jobs:
            target_jobs.append({
                'id': job.id,
                'title': job.title,
                'required_skills': job.required_skills or []
            })
    
    # Get upskilling suggestions
    # Temporarily disabled due to missing database table
    # engine = RecommendationEngine()
    # suggestions = engine.get_upskilling_suggestions(user_skills, target_jobs)
    suggestions = []  # Empty suggestions for now
    
    # Save suggestions to database
    # for suggestion in suggestions:
    #     UpskillingSuggestion.objects.update_or_create(
    #         user=user,
    #         skill_name=suggestion['skill_name'],
    #         defaults={
    #             'current_level': 'beginner',  # Could be determined from resume
    #             'target_level': 'intermediate',
    #             'learning_resources': suggestion['learning_resources'],
    #             'estimated_time_hours': suggestion['estimated_time_hours'],
    #             'difficulty_level': suggestion['difficulty_level'],
    #             'priority_score': suggestion['priority_score']
    #         }
    #     )
    
    # Log recommendation
    RecommendationLog.objects.create(
        user=user,
        resume=resume,
        recommendation_type='skills',
        recommendations=[sug['skill_name'] for sug in suggestions]
    )
    
    return Response({
        'suggestions': suggestions,
        'total_count': len(suggestions)
    })


# Temporarily disabled due to missing database table
# class UpskillingSuggestionListView(generics.ListAPIView):
#     """List upskilling suggestions for current user"""
#     serializer_class = UpskillingSuggestionSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     
#     def get_queryset(self):
#         return UpskillingSuggestion.objects.filter(user=self.request.user).order_by('-priority_score')


# @api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
# def mark_suggestion_completed(request, suggestion_id):
#     """Mark an upskilling suggestion as completed"""
#     suggestion = get_object_or_404(UpskillingSuggestion, id=suggestion_id, user=request.user)
#     
#     completion_percentage = request.data.get('completion_percentage', 100)
#     suggestion.completion_percentage = completion_percentage
#     suggestion.is_completed = completion_percentage >= 100
#     suggestion.save()
#     
#     return Response({
#         'message': 'Suggestion updated successfully',
#         'is_completed': suggestion.is_completed,
#         'completion_percentage': suggestion.completion_percentage
#     })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ml_analytics(request):
    """Get ML analytics and insights"""
    user = request.user
    
    if not user.is_hr:
        return Response(
            {'error': 'Only HR users can view ML analytics'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get analytics for HR's jobs
    hr_jobs = Job.objects.filter(posted_by=user)
    
    # Job match analytics
    job_matches = JobMatchResult.objects.filter(job__in=hr_jobs)
    
    analytics = {
        'total_matches': job_matches.count(),
        'average_match_score': job_matches.aggregate(avg_score=Avg('overall_score'))['avg_score'] or 0,
        'high_quality_matches': job_matches.filter(overall_score__gte=80).count(),
        'skill_extraction_stats': {
            'total_extractions': SkillExtractionResult.objects.count(),
            'average_processing_time': SkillExtractionResult.objects.aggregate(
                avg_time=Avg('processing_time_ms')
            )['avg_time'] or 0,
            'most_common_skills': _get_most_common_skills()
        },
        'recommendation_stats': {
            'total_recommendations': RecommendationLog.objects.count(),
            'average_precision': RecommendationLog.objects.aggregate(
                avg_precision=Avg('precision_at_k')
            )['avg_precision'] or 0
        }
    }
    
    return Response(analytics)


def _get_most_common_skills():
    """Get most commonly extracted skills"""
    from django.db.models import Count
    
    # This is a simplified version - in production, you'd want to properly
    # aggregate across the JSON fields
    skills = []
    recent_extractions = SkillExtractionResult.objects.order_by('-created_at')[:100]
    
    skill_count = {}
    for extraction in recent_extractions:
        for skill in extraction.extracted_skills:
            skill_count[skill] = skill_count.get(skill, 0) + 1
    
    # Sort and return top 10
    sorted_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{'skill': skill, 'count': count} for skill, count in sorted_skills]


class MLModelListView(generics.ListAPIView):
    """List available ML models"""
    serializer_class = MLModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = MLModel.objects.all()


class ModelTrainingLogListView(generics.ListAPIView):
    """List model training logs"""
    serializer_class = ModelTrainingLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        model_id = self.request.query_params.get('model_id', None)
        if model_id:
            return ModelTrainingLog.objects.filter(model_id=model_id)
        return ModelTrainingLog.objects.all()


def recommend_jobs(user):
    """
    Dynamic job recommendation based ONLY on user's uploaded resume skills
    """
    from resumes.models import SkillProfile
    
    # Get user's skill profile - must exist from resume upload
    skill_profile = SkillProfile.objects.filter(user=user).first()
    
    # If no skill profile, user hasn't uploaded a resume
    if not skill_profile or not skill_profile.skills:
        return []
    
    # Get user skills from uploaded resume only
    user_skills = set(skill.lower() for skill in skill_profile.skills.keys())
    
    if not user_skills:
        return []
    
    # Get all active jobs with their skill requirements (optimized query)
    jobs_with_requirements = Job.objects.filter(
        is_active=True
    ).prefetch_related(
        'skill_requirements__skill'
    ).select_related(
        'posted_by'
    )
    
    job_matches = []
    
    for job in jobs_with_requirements:
        # Get job required skills
        job_skills = set()
        for skill_req in job.skill_requirements.all():
            job_skills.add(skill_req.skill.name.lower())
        
        if not job_skills:
            continue
        
        # Calculate match percentage based on overlapping skills
        matching_skills = user_skills.intersection(job_skills)
        match_percentage = (len(matching_skills) / len(job_skills)) * 100
        
        # Only include jobs with some skill match
        if match_percentage > 0:
            job_matches.append({
                'job': job,
                'match_percentage': round(match_percentage, 2),
                'matching_skills': list(matching_skills),
                'total_required_skills': len(job_skills),
                'matched_skills_count': len(matching_skills)
            })
    
    # Sort by match percentage (highest first) and return top 10
    job_matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return job_matches[:10]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recommended_jobs(request):
    """
    API endpoint to get recommended jobs for logged-in user
    GET /api/recommended-jobs/
    
    Returns empty list if no resume uploaded - fully dynamic system
    """
    user = request.user
    
    try:
        # Get job recommendations based on uploaded resume only
        recommendations = recommend_jobs(user)
        
        if not recommendations:
            return Response({
                'message': 'No job recommendations available. Please upload and process a resume first.',
                'recommendations': [],
                'has_resume': False
            })
        
        # Format response with job details
        formatted_recommendations = []
        for rec in recommendations:
            job = rec['job']
            formatted_recommendations.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'requirements': job.requirements,
                'job_type': job.job_type,
                'experience_level': job.experience_level,
                'salary_range': job.salary_range,
                'posted_date': job.posted_date,
                'match_percentage': rec['match_percentage'],
                'matching_skills': rec['matching_skills'],
                'total_required_skills': rec['total_required_skills'],
                'matched_skills_count': rec['matched_skills_count']
            })
        
        return Response({
            'recommendations': formatted_recommendations,
            'total_count': len(formatted_recommendations),
            'has_resume': True,
            'message': f'Found {len(formatted_recommendations)} job recommendations based on your resume skills'
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to get recommendations: {str(e)}',
            'recommendations': [],
            'has_resume': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
