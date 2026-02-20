from django.contrib import admin
from .models import (
    Application, ApplicationStatusHistory, ApplicationDocument, 
    InterviewSchedule, ApplicationFeedback
)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'status', 'match_score', 'applied_at', 'last_status_change']
    list_filter = ['status', 'applied_at', 'match_score']
    search_fields = ['candidate__email', 'job__title', 'job__company']
    readonly_fields = ['applied_at', 'updated_at', 'last_status_change']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('job', 'candidate', 'resume', 'cover_letter', 'additional_notes')
        }),
        ('Match Information', {
            'fields': ('match_score', 'skills_match_score', 'experience_match_score', 'education_match_score')
        }),
        ('Status Information', {
            'fields': ('status', 'hr_notes', 'rejection_reason')
        }),
        ('Metadata', {
            'fields': ('applied_at', 'updated_at', 'last_status_change', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        })
    )


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['application', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['old_status', 'new_status', 'changed_at']
    search_fields = ['application__candidate__email', 'application__job__title']
    readonly_fields = ['changed_at']


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ['application', 'document_type', 'filename', 'file_size', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['application__candidate__email', 'filename']
    readonly_fields = ['uploaded_at', 'file_size']


@admin.register(InterviewSchedule)
class InterviewScheduleAdmin(admin.ModelAdmin):
    list_display = ['application', 'interview_type', 'scheduled_date', 'interviewer', 'is_confirmed', 'is_completed']
    list_filter = ['interview_type', 'is_confirmed', 'is_completed', 'scheduled_date']
    search_fields = ['application__candidate__email', 'interviewer__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Interview Details', {
            'fields': ('application', 'interview_type', 'scheduled_date', 'duration_minutes')
        }),
        ('Location/Link', {
            'fields': ('location', 'meeting_link', 'interviewer')
        }),
        ('Status', {
            'fields': ('is_confirmed', 'is_completed', 'candidate_confirmed')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ApplicationFeedback)
class ApplicationFeedbackAdmin(admin.ModelAdmin):
    list_display = ['application', 'reviewer', 'overall_rating', 'recommendation', 'created_at']
    list_filter = ['recommendation', 'overall_rating', 'created_at']
    search_fields = ['application__candidate__email', 'reviewer__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Feedback Provider', {
            'fields': ('application', 'reviewer')
        }),
        ('Ratings', {
            'fields': ('technical_rating', 'communication_rating', 'culture_fit_rating', 'overall_rating')
        }),
        ('Feedback Content', {
            'fields': ('strengths', 'weaknesses', 'comments', 'recommendation')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
