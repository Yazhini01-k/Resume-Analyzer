from django.db.models import Q, Count, Avg
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    Application, ApplicationStatusHistory, ApplicationDocument,
    InterviewSchedule, ApplicationFeedback
)
from .serializers import (
    ApplicationSerializer, ApplicationCreateSerializer, ApplicationDetailSerializer,
    ApplicationStatusHistorySerializer, ApplicationDocumentSerializer,
    InterviewScheduleSerializer, ApplicationFeedbackSerializer
)
from jobs.models import Job
from resumes.models import Resume
from accounts.models import User


class ApplicationListView(generics.ListAPIView):
    """List applications for current user (candidate) or all applications (HR)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.user.is_hr:
            return ApplicationDetailSerializer
        return ApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_hr:
            # HR can see all applications for their posted jobs
            queryset = Application.objects.filter(job__posted_by=user)
            
            # Filter by status
            status_filter = self.request.query_params.get('status', None)
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            # Filter by job
            job_id = self.request.query_params.get('job_id', None)
            if job_id:
                queryset = queryset.filter(job_id=job_id)
                
        else:
            # Candidates can only see their own applications
            queryset = Application.objects.filter(candidate=user)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from:
            queryset = queryset.filter(applied_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(applied_at__lte=date_to)
        
        return queryset.order_by('-applied_at')


class ApplicationCreateView(generics.CreateAPIView):
    """Create new job application"""
    serializer_class = ApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Store IP and user agent
        serializer.save(
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get application details"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ApplicationDetailSerializer
        return ApplicationSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_hr:
            # HR can see applications for their posted jobs
            return Application.objects.filter(job__posted_by=user)
        else:
            # Candidates can only see their own applications
            return Application.objects.filter(candidate=user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_application_status(request, application_id):
    """Change application status (HR only)"""
    if not request.user.is_hr:
        return Response(
            {'error': 'Only HR users can change application status'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    application = get_object_or_404(Application, id=application_id, job__posted_by=request.user)
    
    new_status = request.data.get('status')
    notes = request.data.get('notes', '')
    
    if new_status not in dict(Application.STATUS_CHOICES):
        return Response(
            {'error': 'Invalid status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Change status
    application.change_status(new_status, notes)
    
    # Send email notification to candidate if status changed to rejected or offered
    if new_status in ['rejected', 'offered']:
        _send_candidate_status_notification(application, new_status)
    
    serializer = ApplicationSerializer(application)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def withdraw_application(request, application_id):
    """Withdraw application (candidate only)"""
    application = get_object_or_404(Application, id=application_id, candidate=request.user)
    
    if application.status in ['rejected', 'offered', 'withdrawn']:
        return Response(
            {'error': 'Cannot withdraw application in current status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    application.change_status('withdrawn', 'Withdrawn by candidate')
    
    return Response({'message': 'Application withdrawn successfully'})


class ApplicationDocumentListView(generics.ListCreateAPIView):
    """List and create application documents"""
    serializer_class = ApplicationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(Application, id=application_id)
        
        # Check permissions
        user = self.request.user
        if user.is_hr:
            if application.job.posted_by != user:
                raise permissions.PermissionDenied("You can only access documents for your job applications")
        else:
            if application.candidate != user:
                raise permissions.PermissionDenied("You can only access your own application documents")
        
        return ApplicationDocument.objects.filter(application=application)
    
    def perform_create(self, serializer):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(Application, id=application_id)
        
        # Check permissions
        user = self.request.user
        if user.is_hr:
            if application.job.posted_by != user:
                raise permissions.PermissionDenied("You can only add documents to your job applications")
        else:
            if application.candidate != user:
                raise permissions.PermissionDenied("You can only add documents to your own applications")
        
        # Set filename and file size
        file = serializer.validated_data['file']
        serializer.save(
            application=application,
            filename=file.name,
            file_size=file.size
        )


class InterviewScheduleView(generics.RetrieveUpdateAPIView):
    """Get or update interview schedule"""
    serializer_class = InterviewScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(Application, id=application_id)
        
        # Check permissions
        user = self.request.user
        if user.is_hr:
            if application.job.posted_by != user:
                raise permissions.PermissionDenied("You can only access interviews for your job applications")
        else:
            if application.candidate != user:
                raise permissions.PermissionDenied("You can only access your own interviews")
        
        interview, created = InterviewSchedule.objects.get_or_create(application=application)
        return interview


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_interview(request, application_id):
    """Confirm interview (candidate only)"""
    application = get_object_or_404(Application, id=application_id, candidate=request.user)
    
    try:
        interview = application.interview
        interview.candidate_confirmed = True
        interview.save()
        
        return Response({'message': 'Interview confirmed successfully'})
    except InterviewSchedule.DoesNotExist:
        return Response(
            {'error': 'No interview scheduled for this application'},
            status=status.HTTP_404_NOT_FOUND
        )


class ApplicationFeedbackView(generics.ListCreateAPIView):
    """List and create application feedback"""
    serializer_class = ApplicationFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(Application, id=application_id)
        
        # Only HR can see feedback
        if not self.request.user.is_hr or application.job.posted_by != self.request.user:
            raise permissions.PermissionDenied("Only HR can view feedback")
        
        return ApplicationFeedback.objects.filter(application=application)
    
    def perform_create(self, serializer):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(Application, id=application_id)
        
        # Only HR can create feedback
        if not self.request.user.is_hr or application.job.posted_by != self.request.user:
            raise permissions.PermissionDenied("Only HR can create feedback")
        
        serializer.save(
            application=application,
            reviewer=self.request.user
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def application_statistics(request):
    """Get application statistics for HR dashboard"""
    if not request.user.is_hr:
        return Response(
            {'error': 'Only HR users can view statistics'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user = request.user
    
    # Basic stats
    total_applications = Application.objects.filter(job__posted_by=user).count()
    pending_applications = Application.objects.filter(job__posted_by=user, status='pending').count()
    shortlisted_applications = Application.objects.filter(job__posted_by=user, status='shortlisted').count()
    
    # Recent applications
    recent_applications = Application.objects.filter(
        job__posted_by=user
    ).order_by('-applied_at')[:10]
    
    # Applications by status
    status_stats = Application.objects.filter(job__posted_by=user).values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Average match scores
    avg_match_score = Application.objects.filter(job__posted_by=user).aggregate(
        avg_score=Avg('match_score')
    )['avg_score'] or 0
    
    return Response({
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'shortlisted_applications': shortlisted_applications,
        'average_match_score': round(avg_match_score, 1),
        'status_breakdown': list(status_stats),
        'recent_applications': ApplicationSerializer(recent_applications, many=True).data
    })


def _send_candidate_status_notification(application, new_status):
    """Send email notification to candidate about status change"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        if new_status == 'rejected':
            subject = f"Application Status Update: {application.job.title}"
            message = f"""
            Dear {application.candidate.get_full_name()},
            
            Thank you for your interest in the {application.job.title} position at {application.job.company}.
            
            After careful consideration, we have decided to move forward with other candidates whose qualifications better match our current needs.
            
            We appreciate you taking the time to apply and wish you the best in your job search.
            
            Best regards,
            {application.job.posted_by.get_full_name()}
            {application.job.company}
            """
        elif new_status == 'offered':
            subject = f"Job Offer: {application.job.title} at {application.job.company}"
            message = f"""
            Dear {application.candidate.get_full_name()},
            
            Congratulations! We are pleased to offer you the position of {application.job.title} at {application.job.company}.
            
            We were very impressed with your qualifications and believe you would be a great addition to our team.
            
            Please contact us at your earliest convenience to discuss the offer details.
            
            Best regards,
            {application.job.posted_by.get_full_name()}
            {application.job.company}
            """
        else:
            return
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [application.candidate.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send candidate notification: {e}")
