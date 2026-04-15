from django.db.models import Q, Count
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Job, JobCategory, JobSkill, JobMatch
from .serializers import (
    JobSerializer, JobCreateSerializer, JobCategorySerializer, 
    JobSkillSerializer, JobMatchSerializer, JobRecommendationSerializer
)
from .utils import JobMatcher
from .recommendation_engine import recommendation_engine
from resumes.models import Resume
from accounts.models import User


class JobListView(generics.ListAPIView):
    """List all active jobs"""
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True)
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(company__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
        
        # Filter by location
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by job type
        job_type = self.request.query_params.get('job_type', None)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        # Filter by experience level
        experience_level = self.request.query_params.get('experience_level', None)
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)
        
        # Filter by skills
        skills = self.request.query_params.get('skills', None)
        if skills:
            skill_list = [skill.strip() for skill in skills.split(',')]
            for skill in skill_list:
                queryset = queryset.filter(
                    Q(required_skills__icontains=skill) |
                    Q(preferred_skills__icontains=skill)
                )
        
        return queryset.distinct()


class JobDetailView(generics.RetrieveAPIView):
    """Get job details"""
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class JobCreateView(generics.CreateAPIView):
    """Create new job posting (HR only)"""
    serializer_class = JobCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Check if user is HR
        if not self.request.user.is_hr:
            raise permissions.PermissionDenied("Only HR users can post jobs")
        
        serializer.save(posted_by=self.request.user)


class JobUpdateView(generics.UpdateAPIView):
    """Update job posting (HR only)"""
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.all()
    
    def get_object(self):
        obj = super().get_object()
        # Check if user is the job poster
        if obj.posted_by != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only edit your own job postings")
        return obj


class JobDeleteView(generics.DestroyAPIView):
    """Delete job posting (HR only)"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.all()
    
    def get_object(self):
        obj = super().get_object()
        # Check if user is the job poster
        if obj.posted_by != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only delete your own job postings")
        return obj




@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_posted_jobs(request):
    """Get jobs posted by current HR user"""
    if not request.user.is_hr:
        return Response(
            {'error': 'Only HR users can view posted jobs'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    jobs = Job.objects.filter(posted_by=request.user)
    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def rank_candidates_for_job(request, job_id):
    """Rank candidates for a specific job (HR only)"""
    if not request.user.is_hr:
        return Response(
            {'error': 'Only HR users can rank candidates'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    
    # Get threshold from request
    threshold = request.data.get('threshold', 30.0)
    
    # Get all matches for this job above threshold with related data
    matches = JobMatch.objects.filter(
        job=job,
        overall_score__gte=threshold
    ).select_related('resume', 'user', 'resume__user').order_by('-overall_score')
    
    # Serialize matches
    serializer = JobMatchSerializer(matches, many=True)
    
    return Response({
        'job': JobSerializer(job).data,
        'candidates': serializer.data,
        'threshold': threshold,
        'total_candidates': matches.count()
    })


class JobCategoryListView(generics.ListAPIView):
    """List job categories"""
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class JobSkillListView(generics.ListAPIView):
    """List job skills"""
    queryset = JobSkill.objects.all()
    serializer_class = JobSkillSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = JobSkill.objects.all()
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset




@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_skills_summary(request):
    """
    Get a summary of user's skills from their resume.
    """
    user = request.user
    
    try:
        from resumes.models import Resume
        
        # Get user's latest processed resume
        latest_resume = Resume.objects.filter(
            user=user,
            processing_status='completed'
        ).order_by('-created_at').first()
        
        if not latest_resume:
            return Response(
                {'error': 'No processed resume found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return skills summary
        return Response({
            'skills': latest_resume.extracted_skills or [],
            'total_skills': len(latest_resume.extracted_skills or []),
            'resume_title': latest_resume.title,
            'processed_at': latest_resume.updated_at.isoformat(),
            'status': 'success'
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get skills summary: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
