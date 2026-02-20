from django.contrib import admin
from .models import Job, JobCategory, JobSkill, JobSkillRequirement, JobMatch


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'job_type', 'experience_level', 
                   'is_active', 'application_count', 'view_count', 'created_at']
    list_filter = ['job_type', 'experience_level', 'is_active', 'created_at']
    search_fields = ['title', 'company', 'location', 'description']
    readonly_fields = ['application_count', 'view_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'location', 'description', 'requirements', 'responsibilities')
        }),
        ('Job Details', {
            'fields': ('salary_range', 'job_type', 'experience_level', 'deadline')
        }),
        ('Skills Data', {
            'fields': ('required_skills', 'preferred_skills', 'skill_keywords', 'feature_vector')
        }),
        ('Metadata', {
            'fields': ('posted_by', 'is_active', 'external_url', 'company_logo')
        }),
        ('Statistics', {
            'fields': ('application_count', 'view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']
    search_fields = ['name', 'description']
    list_filter = ['parent']


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    search_fields = ['name', 'category']
    list_filter = ['category']


@admin.register(JobSkillRequirement)
class JobSkillRequirementAdmin(admin.ModelAdmin):
    list_display = ['job', 'skill', 'importance', 'experience_years']
    list_filter = ['importance', 'skill__category']
    search_fields = ['job__title', 'skill__name']


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ['resume', 'job', 'overall_score', 'skills_match_score', 'recommendation_rank', 'created_at']
    list_filter = ['overall_score', 'recommendation_rank', 'created_at']
    search_fields = ['resume__title', 'job__title', 'job__company']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Match Information', {
            'fields': ('resume', 'job', 'overall_score', 'recommendation_rank')
        }),
        ('Score Breakdown', {
            'fields': ('skills_match_score', 'experience_match_score', 'education_match_score')
        }),
        ('Match Details', {
            'fields': ('matched_skills', 'missing_skills', 'additional_skills', 'match_reason')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        })
    )
