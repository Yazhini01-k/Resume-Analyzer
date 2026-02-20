from django.contrib import admin
from .models import Resume, SkillProfile, ResumeAnalysis


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'file_type', 'processing_status', 'overall_score', 'created_at']
    list_filter = ['processing_status', 'file_type', 'created_at']
    search_fields = ['title', 'user__email', 'original_filename']
    readonly_fields = ['created_at', 'updated_at', 'file_size']
    
    def overall_score(self, obj):
        try:
            return obj.analysis.overall_score
        except ResumeAnalysis.DoesNotExist:
            return "Not analyzed"
    overall_score.short_description = 'Overall Score'


@admin.register(SkillProfile)
class SkillProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_skills_count', 'last_updated']
    search_fields = ['user__email']
    readonly_fields = ['last_updated']


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ['resume', 'overall_score', 'completeness_score', 'skills_score', 'created_at']
    list_filter = ['overall_score', 'created_at']
    search_fields = ['resume__title', 'resume__user__email']
    readonly_fields = ['created_at', 'updated_at']
