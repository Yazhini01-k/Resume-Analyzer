from rest_framework import serializers
from .models import (
    MLModel, SkillExtractionResult, JobMatchResult, RecommendationLog,
    UpskillingSuggestion, ModelTrainingLog
)


class MLModelSerializer(serializers.ModelSerializer):
    """Serializer for MLModel"""
    
    class Meta:
        model = MLModel
        fields = ['id', 'name', 'model_type', 'version', 'file_path', 'accuracy', 
                 'precision', 'recall', 'f1_score', 'training_samples', 'training_date',
                 'is_active', 'is_deployed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SkillExtractionResultSerializer(serializers.ModelSerializer):
    """Serializer for SkillExtractionResult"""
    
    class Meta:
        model = SkillExtractionResult
        fields = ['id', 'resume', 'extracted_skills', 'confidence_scores', 
                 'processing_time_ms', 'model_version', 'created_at']
        read_only_fields = ['id', 'created_at']


class JobMatchResultSerializer(serializers.ModelSerializer):
    """Serializer for JobMatchResult"""
    resume_title = serializers.CharField(source='resume.title', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_company = serializers.CharField(source='job.company', read_only=True)
    
    class Meta:
        model = JobMatchResult
        fields = ['id', 'resume', 'resume_title', 'job', 'job_title', 'job_company',
                 'overall_score', 'skills_score', 'experience_score', 'education_score',
                 'matched_skills', 'missing_skills', 'skill_gap_analysis', 
                 'processing_time_ms', 'algorithm_version', 'created_at']
        read_only_fields = ['id', 'created_at']


class RecommendationLogSerializer(serializers.ModelSerializer):
    """Serializer for RecommendationLog"""
    
    class Meta:
        model = RecommendationLog
        fields = ['id', 'user', 'resume', 'recommendation_type', 'recommendations',
                 'user_interactions', 'precision_at_k', 'recall_at_k', 'diversity_score',
                 'created_at']
        read_only_fields = ['id', 'created_at']


class UpskillingSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for UpskillingSuggestion"""
    
    class Meta:
        model = UpskillingSuggestion
        fields = ['id', 'skill_name', 'current_level', 'target_level', 'learning_resources',
                 'estimated_time_hours', 'difficulty_level', 'priority_score', 
                 'market_demand_score', 'salary_impact_score', 'is_completed', 
                 'completion_percentage', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModelTrainingLogSerializer(serializers.ModelSerializer):
    """Serializer for ModelTrainingLog"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelTrainingLog
        fields = ['id', 'model', 'model_name', 'training_data_size', 'validation_data_size',
                 'test_data_size', 'hyperparameters', 'training_algorithm', 'training_loss',
                 'validation_loss', 'training_time_minutes', 'final_accuracy', 'final_precision',
                 'final_recall', 'final_f1_score', 'status', 'error_message',
                 'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at']
