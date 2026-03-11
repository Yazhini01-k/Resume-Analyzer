from django.db import models
from django.contrib.auth import get_user_model
from jobs.models import Job
from resumes.models import Resume

User = get_user_model()


class Application(models.Model):
    """Job application model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('interviewed', 'Interviewed'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    # Application details
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='applications')
    
    # Application content
    cover_letter = models.TextField(blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)
    
    # Detailed candidate information
    education_details = models.JSONField(default=list, blank=True, help_text="Education details from resume")
    skills_details = models.JSONField(default=list, blank=True, help_text="Skills details from resume")
    experience_details = models.JSONField(default=list, blank=True, help_text="Experience details from resume")
    
    # Additional candidate-provided information
    cgpa = models.CharField(max_length=20, blank=True, null=True, help_text="Candidate's CGPA")
    arrears_history = models.TextField(blank=True, null=True, help_text="History of arrears/backlogs")
    internships = models.TextField(blank=True, null=True, help_text="Internship experience details")
    technical_skills = models.TextField(blank=True, null=True, help_text="Technical skills list")
    
    # Match information
    match_score = models.FloatField(default=0.0)  # Overall match score
    skills_match_score = models.FloatField(default=0.0)
    experience_match_score = models.FloatField(default=0.0)
    education_match_score = models.FloatField(default=0.0)
    
    # Application status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    hr_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_status_change = models.DateTimeField(auto_now=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['job', 'candidate']
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['applied_at']),
            models.Index(fields=['match_score']),
        ]
    
    def __str__(self):
        return f"{self.candidate.email} - {self.job.title}"
    
    def change_status(self, new_status, notes=None):
        """Change application status with history tracking"""
        from django.utils import timezone
        old_status = self.status
        self.status = new_status
        self.last_status_change = timezone.now()
        
        if notes:
            self.hr_notes = notes
        
        # Create status change history
        ApplicationStatusHistory.objects.create(
            application=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=None,  # Will be set in view
            notes=notes
        )
        
        self.save()
    
    def save(self, *args, **kwargs):
        # Increment job application count on first creation
        if not self.pk:
            self.job.increment_application_count()
        super().save(*args, **kwargs)


class ApplicationStatusHistory(models.Model):
    """Track application status changes"""
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.application} - {self.old_status} to {self.new_status}"


class ApplicationDocument(models.Model):
    """Additional documents for applications"""
    
    DOCUMENT_TYPES = [
        ('cover_letter', 'Cover Letter'),
        ('portfolio', 'Portfolio'),
        ('certification', 'Certification'),
        ('transcript', 'Transcript'),
        ('other', 'Other'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='application_documents/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.application} - {self.document_type}"


class InterviewSchedule(models.Model):
    """Interview scheduling for applications"""
    
    INTERVIEW_TYPES = [
        ('phone', 'Phone Screen'),
        ('video', 'Video Interview'),
        ('technical', 'Technical Interview'),
        ('behavioral', 'Behavioral Interview'),
        ('onsite', 'On-site Interview'),
        ('final', 'Final Interview'),
    ]
    
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='interview')
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    location = models.CharField(max_length=255, blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    interviewer = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='interviews')
    notes = models.TextField(blank=True, null=True)
    
    # Status
    is_confirmed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    candidate_confirmed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Interview for {self.application} - {self.interview_type}"


class ApplicationFeedback(models.Model):
    """Feedback for applications"""
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='feedback')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Ratings (1-5 scale)
    technical_rating = models.IntegerField(blank=True, null=True)
    communication_rating = models.IntegerField(blank=True, null=True)
    culture_fit_rating = models.IntegerField(blank=True, null=True)
    overall_rating = models.IntegerField(blank=True, null=True)
    
    # Feedback content
    strengths = models.TextField(blank=True, null=True)
    weaknesses = models.TextField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('strong_hire', 'Strong Hire'),
            ('hire', 'Hire'),
            ('maybe', 'Maybe'),
            ('no_hire', 'No Hire'),
        ],
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['application', 'reviewer']
    
    def __str__(self):
        return f"Feedback for {self.application} by {self.reviewer.email}"
