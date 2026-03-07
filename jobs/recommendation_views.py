"""
Enhanced Views for Dynamic Job Recommendations
Handles real-time job recommendations based on resume skills
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Avg, F, Min, Max
from django.http import JsonResponse
import json

from .models import Job, JobMatch
from .recommendation_engine import recommendation_engine
from resumes.models import Resume, SkillProfile
from applications.models import Application

User = get_user_model()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_dynamic_recommendations(request):
    """
    Get dynamic job recommendations based on user's resume skills
    """
    user = request.user
    
    if user.role != 'candidate':
        return Response(
            {'error': 'This endpoint is only available for candidates'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get recommendations using the engine
        limit = int(request.GET.get('limit', 10))
        min_score = float(request.GET.get('min_score', 30.0))
        
        recommendations = recommendation_engine.get_user_recommendations(
            user=user,
            limit=limit,
            min_score=min_score
        )
        
        # Format response
        response_data = {
            'recommendations': [],
            'total_count': len(recommendations),
            'generated_at': timezone.now().isoformat(),
            'min_score_used': min_score
        }
        
        for rec in recommendations:
            job_data = {
                'id': rec['job'].id,
                'title': rec['job'].title,
                'company': rec['job'].company,
                'location': rec['job'].location,
                'description': rec['job'].description,
                'requirements': rec['job'].requirements,
                'responsibilities': rec['job'].responsibilities,
                'salary_range': rec['job'].salary_range,
                'salary_min': rec['job'].salary_min,
                'salary_max': rec['job'].salary_max,
                'job_type': rec['job'].job_type,
                'experience_level': rec['job'].experience_level,
                'required_skills': rec['job'].required_skills,
                'preferred_skills': rec['job'].preferred_skills,
                'is_active': rec['job'].is_active,
                'application_count': rec['job'].application_count,
                'view_count': rec['job'].view_count,
                'created_at': rec['job'].created_at.isoformat(),
                'deadline': rec['job'].deadline.isoformat() if rec['job'].deadline else None,
                'external_url': rec['job'].external_url,
                'company_logo': rec['job'].company_logo.url if rec['job'].company_logo else None,
                
                # Match information - include all score breakdowns from ML engine
                'match_percentage': rec['match'].overall_score,
                'overall_score': rec['match'].overall_score,
                'skills_match_score': rec['match'].skills_match_score,
                'experience_match_score': rec['match'].experience_match_score,
                'education_match_score': rec['match'].education_match_score,
                'location_match_score': rec['match'].location_match_score,
                'salary_match_score': rec['match'].salary_match_score,
                'matched_skills': rec['match'].matched_skills,
                'missing_skills': rec['match'].missing_skills,
                'match_reason': rec['match'].match_reason,
                'match_id': rec['match'].id,
                'is_viewed': rec['match'].is_viewed,
                'is_applied': rec['match'].is_applied,
                'is_saved': rec['match'].is_saved,
                'confidence_level': rec['match'].confidence_level,
                'recommendation_source': rec['match'].recommendation_source,
                'created_at': rec['match'].created_at.isoformat(),
                'expires_at': rec['match'].expires_at.isoformat() if rec['match'].expires_at else None
            }
            
            response_data['recommendations'].append(job_data)
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to generate recommendations: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_recommendations(request):
    """
    Refresh recommendations for the current user
    """
    user = request.user
    
    if user.role != 'candidate':
        return Response(
            {'error': 'This endpoint is only available for candidates'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Refresh recommendations
        recommendations = recommendation_engine.refresh_recommendations_for_user(user)
        
        return Response({
            'message': 'Recommendations refreshed successfully',
            'new_recommendations_count': len(recommendations),
            'refreshed_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to refresh recommendations: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_recommendation_viewed(request, match_id):
    """
    Mark a recommendation as viewed
    """
    try:
        job_match = get_object_or_404(JobMatch, id=match_id, user=request.user)
        
        if job_match.is_viewed:
            return Response({'message': 'Already marked as viewed'})
        
        job_match.mark_viewed()
        
        # Increment job view count
        job_match.job.increment_view_count()
        
        return Response({
            'message': 'Marked as viewed',
            'viewed_at': job_match.viewed_at.isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to mark as viewed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_recommendation(request, match_id):
    """
    Save a recommendation for later
    """
    try:
        job_match = get_object_or_404(JobMatch, id=match_id, user=request.user)
        
        if job_match.is_saved:
            # Unsave if already saved
            job_match.is_saved = False
            job_match.saved_at = None
            message = 'Recommendation unsaved'
        else:
            job_match.mark_saved()
            message = 'Recommendation saved'
        
        job_match.save()
        
        return Response({
            'message': message,
            'is_saved': job_match.is_saved,
            'saved_at': job_match.saved_at.isoformat() if job_match.saved_at else None
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to save recommendation: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_recommendation_analytics(request):
    """
    Get analytics about user's recommendations
    """
    user = request.user
    
    if user.role != 'candidate':
        return Response(
            {'error': 'This endpoint is only available for candidates'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        analytics = recommendation_engine.get_recommendation_analytics(user)
        
        return Response({
            'analytics': analytics,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get analytics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_skill_analysis(request):
    """
    Get detailed skill analysis for the user
    """
    user = request.user
    
    if user.role != 'candidate':
        return Response(
            {'error': 'This endpoint is only available for candidates'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get user's latest resume
        latest_resume = Resume.objects.filter(
            user=user,
            processing_status='completed'
        ).order_by('-created_at').first()
        
        if not latest_resume:
            return Response({'error': 'No processed resume found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get skill profile
        skill_profile = getattr(user, 'skill_profile', None)
        
        # Analyze skills
        skills_data = {
            'total_skills': len(latest_resume.extracted_skills) if latest_resume.extracted_skills else 0,
            'extracted_skills': latest_resume.extracted_skills or [],
            'skill_profile': skill_profile.skills if skill_profile else {},
            'verification_status': skill_profile.verification_status if skill_profile else 'none',
            'last_assessed': skill_profile.last_assessed.isoformat() if skill_profile else None
        }
        
        # Get job market demand for these skills
        skill_demand = {}
        if latest_resume.extracted_skills:
            for skill in latest_resume.extracted_skills:
                # Count jobs requiring this skill
                job_count = Job.objects.filter(
                    is_active=True,
                    required_skills__contains=[skill]
                ).count()
                
                skill_demand[skill] = {
                    'job_count': job_count,
                    'demand_level': 'high' if job_count > 20 else 'medium' if job_count > 5 else 'low'
                }
        
        return Response({
            'skills_analysis': skills_data,
            'skill_demand': skill_demand,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get skill analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_job_market_insights(request):
    """
    Get job market insights based on user's skills
    """
    user = request.user
    
    if user.role != 'candidate':
        return Response(
            {'error': 'This endpoint is only available for candidates'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get user's skills
        latest_resume = Resume.objects.filter(
            user=user,
            processing_status='completed'
        ).order_by('-created_at').first()
        
        if not latest_resume or not latest_resume.extracted_skills:
            return Response({'error': 'No skills found'}, status=status.HTTP_404_NOT_FOUND)
        
        user_skills = latest_resume.extracted_skills
        
        # Market insights
        insights = {
            'total_active_jobs': Job.objects.filter(is_active=True).count(),
            'jobs_matching_skills': 0,
            'top_companies': [],
            'top_locations': [],
            'salary_ranges': {},
            'skill_demand': {}
        }
        
        # Find jobs matching user's skills
        matching_jobs = Job.objects.filter(
            is_active=True
        ).filter(
            Q(required_skills__overlap=user_skills) | 
            Q(preferred_skills__overlap=user_skills)
        )
        
        insights['jobs_matching_skills'] = matching_jobs.count()
        
        # Top companies for matching jobs
        top_companies = matching_jobs.values('company').annotate(
            job_count=Count('id')
        ).order_by('-job_count')[:10]
        
        insights['top_companies'] = list(top_companies)
        
        # Top locations for matching jobs
        top_locations = matching_jobs.values('location').annotate(
            job_count=Count('id')
        ).order_by('-job_count')[:10]
        
        insights['top_locations'] = list(top_locations)
        
        # Salary ranges
        salary_data = matching_jobs.aggregate(
            avg_min=Avg('salary_min'),
            avg_max=Avg('salary_max'),
            min_salary=Min('salary_min'),
            max_salary=Max('salary_max')
        )
        
        insights['salary_ranges'] = salary_data
        
        # Individual skill demand
        for skill in user_skills:
            skill_jobs = Job.objects.filter(
                is_active=True,
                required_skills__contains=[skill]
            )
            
            insights['skill_demand'][skill] = {
                'job_count': skill_jobs.count(),
                'avg_salary_min': skill_jobs.aggregate(Avg('salary_min'))['salary_min__avg'] or 0,
                'top_companies': list(skill_jobs.values('company').annotate(
                    count=Count('id')
                ).order_by('-count')[:5])
            }
        
        return Response({
            'insights': insights,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get market insights: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_jobs_by_skills(request):
    """
    Search jobs based on specific skills
    """
    user = request.user
    
    if user.role != 'candidate':
        return Response(
            {'error': 'This endpoint is only available for candidates'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get skills from query parameter
        skills_param = request.GET.get('skills', '')
        if not skills_param:
            return Response({'error': 'Skills parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        skills = [skill.strip() for skill in skills_param.split(',') if skill.strip()]
        
        # Search jobs
        jobs = Job.objects.filter(
            is_active=True
        ).filter(
            Q(required_skills__overlap=skills) | 
            Q(preferred_skills__overlap=skills)
        ).select_related('posted_by').order_by('-created_at')
        
        # Calculate match scores for each job
        job_results = []
        for job in jobs:
            match_score = job.calculate_skill_match(skills)
            if match_score >= 20.0:  # Minimum threshold
                job_results.append({
                    'job': job,
                    'match_score': match_score,
                    'matched_skills': list(set(skills) & set(job.required_skills))
                })
        
        # Sort by match score
        job_results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Format response
        response_data = {
            'search_query': skills,
            'total_results': len(job_results),
            'jobs': []
        }
        
        for result in job_results[:20]:  # Limit to 20 results
            job = result['job']
            response_data['jobs'].append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description[:200] + '...' if len(job.description) > 200 else job.description,
                'salary_range': job.salary_range,
                'job_type': job.job_type,
                'experience_level': job.experience_level,
                'required_skills': job.required_skills,
                'preferred_skills': job.preferred_skills,
                'match_score': result['match_score'],
                'matched_skills': result['matched_skills'],
                'created_at': job.created_at.isoformat(),
                'application_count': job.application_count
            })
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to search jobs: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
