from rest_framework import serializers
from .models import Resume, SkillProfile, ResumeAnalysis


class ResumeSerializer(serializers.ModelSerializer):
    """Serializer for Resume model"""
    
    class Meta:
        model = Resume
        fields = ['id', 'title', 'file', 'original_filename', 'raw_text', 
                 'processed_text', 'extracted_skills', 'extracted_education', 
                 'extracted_experience', 'extracted_contact_info', 'feature_vector',
                 'skill_keywords', 'file_size', 'file_type', 'processing_status',
                 'error_message', 'created_at', 'updated_at']
        read_only_fields = ['id', 'raw_text', 'processed_text', 'extracted_skills',
                           'extracted_education', 'extracted_experience', 
                           'extracted_contact_info', 'feature_vector', 'skill_keywords',
                           'file_size', 'file_type', 'processing_status', 
                           'error_message', 'created_at', 'updated_at']


class ResumeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Resume (file upload)"""
    
    class Meta:
        model = Resume
        fields = ['title', 'file']
    
    def validate_file(self, value):
        # Check file size (5MB limit)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 5MB")
        
        # Check file type
        allowed_extensions = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
        file_extension = value.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for Resume Analysis"""
    
    class Meta:
        model = ResumeAnalysis
        fields = ['resume', 'completeness_score', 'skills_score', 'experience_score',
                 'education_score', 'overall_score', 'missing_skills', 
                 'improvement_suggestions', 'skill_gaps', 'word_count', 
                 'sentence_count', 'readability_score', 'created_at', 'updated_at']
        read_only_fields = ['resume', 'created_at', 'updated_at']


class SkillProfileSerializer(serializers.ModelSerializer):
    """Serializer for Skill Profile"""
    
    class Meta:
        model = SkillProfile
        fields = ['skills', 'total_skills_count', 'last_updated']
        read_only_fields = ['total_skills_count', 'last_updated']


class ResumeDetailSerializer(ResumeSerializer):
    """Detailed Resume serializer including analysis"""
    analysis = ResumeAnalysisSerializer(read_only=True)
    
    class Meta(ResumeSerializer.Meta):
        fields = ResumeSerializer.Meta.fields + ['analysis']
