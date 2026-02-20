from rest_framework import serializers
from .models import (
    Application, ApplicationStatusHistory, ApplicationDocument,
    InterviewSchedule, ApplicationFeedback
)
from jobs.serializers import JobSerializer
from resumes.serializers import ResumeSerializer
from accounts.serializers import UserSerializer


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Application model"""
    candidate_details = UserSerializer(source='candidate', read_only=True)
    job_details = JobSerializer(source='job', read_only=True)
    resume_details = ResumeSerializer(source='resume', read_only=True)
    
    class Meta:
        model = Application
        fields = ['id', 'job', 'candidate', 'resume', 'cover_letter', 'additional_notes',
                 'education_details', 'skills_details', 'experience_details',
                 'cgpa', 'arrears_history', 'internships', 'technical_skills',
                 'match_score', 'skills_match_score', 'experience_match_score', 
                 'education_match_score', 'status', 'hr_notes', 'rejection_reason',
                 'applied_at', 'updated_at', 'last_status_change', 'candidate_details',
                 'job_details', 'resume_details']
        read_only_fields = ['id', 'candidate', 'match_score', 'skills_match_score',
                           'experience_match_score', 'education_match_score', 'applied_at',
                           'updated_at', 'last_status_change']


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications"""
    
    class Meta:
        model = Application
        fields = ['job', 'resume', 'cover_letter', 'additional_notes', 
                 'education_details', 'skills_details', 'experience_details',
                 'cgpa', 'arrears_history', 'internships', 'technical_skills']
    
    def validate(self, attrs):
        user = self.context['request'].user
        job = attrs['job']
        resume = attrs['resume']
        
        # Check if user owns the resume
        if resume.user != user:
            raise serializers.ValidationError("You can only use your own resume")
        
        # Check if already applied
        if Application.objects.filter(candidate=user, job=job).exists():
            raise serializers.ValidationError("You have already applied to this job")
        
        # Check if job is still active
        if not job.is_active:
            raise serializers.ValidationError("This job is no longer active")
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        job = validated_data['job']
        resume = validated_data['resume']
        
        # Get match score from JobMatch if available
        from jobs.models import JobMatch
        try:
            job_match = JobMatch.objects.get(resume=resume, job=job)
            match_score = job_match.overall_score
            skills_score = job_match.skills_match_score
            experience_score = job_match.experience_match_score
            education_score = job_match.education_match_score
        except JobMatch.DoesNotExist:
            match_score = 0.0
            skills_score = 0.0
            experience_score = 0.0
            education_score = 0.0
        
        # Create application
        application = Application.objects.create(
            candidate=user,
            match_score=match_score,
            skills_match_score=skills_score,
            experience_match_score=experience_score,
            education_match_score=education_score,
            **validated_data
        )
        
        # Send email notification to HR
        self._send_hr_notification(application)
        
        return application
    
    def _send_hr_notification(self, application):
        """Send email notification to HR about new application"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        try:
            subject = f"New Application: {application.candidate.get_full_name()} for {application.job.title}"
            
            message = f"""
            New application received:
            
            Candidate: {application.candidate.get_full_name()} ({application.candidate.email})
            Position: {application.job.title} at {application.job.company}
            Applied: {application.applied_at.strftime('%Y-%m-%d %H:%M')}
            Match Score: {application.match_score:.1f}%
            
            Resume: {application.resume.title}
            Cover Letter: {'Yes' if application.cover_letter else 'No'}
            
            EDUCATION DETAILS:
            CGPA: {application.cgpa or 'Not provided'}
            Education: {application.education_details if application.education_details else 'Not available'}
            
            SKILLS & EXPERIENCE:
            Technical Skills: {application.technical_skills or 'Not provided'}
            Skills from Resume: {application.skills_details if application.skills_details else 'Not available'}
            Experience: {application.experience_details if application.experience_details else 'Not available'}
            
            ADDITIONAL INFO:
            Arrears History: {application.arrears_history or 'None'}
            Internships: {application.internships or 'Not provided'}
            Additional Notes: {application.additional_notes or 'None'}
            
            View application in dashboard: {settings.DEFAULT_FROM_EMAIL}
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [application.job.posted_by.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't fail the application
            print(f"Failed to send HR notification: {e}")


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for ApplicationStatusHistory"""
    changed_by_details = UserSerializer(source='changed_by', read_only=True)
    
    class Meta:
        model = ApplicationStatusHistory
        fields = ['id', 'old_status', 'new_status', 'changed_by', 'changed_by_details',
                 'notes', 'changed_at']
        read_only_fields = ['id', 'changed_at']


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    """Serializer for ApplicationDocument"""
    
    class Meta:
        model = ApplicationDocument
        fields = ['id', 'document_type', 'file', 'filename', 'file_size', 'uploaded_at']
        read_only_fields = ['id', 'filename', 'file_size', 'uploaded_at']
    
    def validate_file(self, value):
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        return value


class InterviewScheduleSerializer(serializers.ModelSerializer):
    """Serializer for InterviewSchedule"""
    interviewer_details = UserSerializer(source='interviewer', read_only=True)
    
    class Meta:
        model = InterviewSchedule
        fields = ['id', 'application', 'interview_type', 'scheduled_date', 'duration_minutes',
                 'location', 'meeting_link', 'interviewer', 'interviewer_details', 'notes',
                 'is_confirmed', 'is_completed', 'candidate_confirmed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApplicationFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for ApplicationFeedback"""
    reviewer_details = UserSerializer(source='reviewer', read_only=True)
    
    class Meta:
        model = ApplicationFeedback
        fields = ['id', 'application', 'reviewer', 'reviewer_details', 'technical_rating',
                 'communication_rating', 'culture_fit_rating', 'overall_rating', 'strengths',
                 'weaknesses', 'comments', 'recommendation', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        # Validate rating ranges
        rating_fields = ['technical_rating', 'communication_rating', 'culture_fit_rating', 'overall_rating']
        for field in rating_fields:
            if field in attrs and attrs[field] is not None:
                if not 1 <= attrs[field] <= 5:
                    raise serializers.ValidationError(f"{field} must be between 1 and 5")
        return attrs


class ApplicationDetailSerializer(ApplicationSerializer):
    """Detailed application serializer including related data"""
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    interview = InterviewScheduleSerializer(read_only=True)
    feedback = ApplicationFeedbackSerializer(many=True, read_only=True)
    
    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + ['status_history', 'documents', 'interview', 'feedback']
