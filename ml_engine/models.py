from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MLModel(models.Model):
    """Store trained ML models and their metadata"""
    
    MODEL_TYPES = [
        ('skill_extractor', 'Skill Extractor'),
        ('job_matcher', 'Job Matcher'),
        ('resume_analyzer', 'Resume Analyzer'),
        ('recommendation', 'Recommendation System'),
    ]
    
    name = models.CharField(max_length=200)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=50)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    
    # Model metadata
    accuracy = models.FloatField(blank=True, null=True)
    precision = models.FloatField(blank=True, null=True)
    recall = models.FloatField(blank=True, null=True)
    f1_score = models.FloatField(blank=True, null=True)
    
    # Training data info
    training_samples = models.IntegerField(default=0)
    training_date = models.DateTimeField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=False)
    is_deployed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.model_type})"


class SkillExtractionResult(models.Model):
    """Store skill extraction results for analytics"""
    
    resume = models.ForeignKey('resumes.Resume', on_delete=models.CASCADE, related_name='skill_extraction_results')
    extracted_skills = models.JSONField(default=list)
    confidence_scores = models.JSONField(default=dict)
    processing_time_ms = models.IntegerField(default=0)
    model_version = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Skill extraction for {self.resume.title}"


class JobMatchResult(models.Model):
    """Store job matching results for analytics"""
    
    resume = models.ForeignKey('resumes.Resume', on_delete=models.CASCADE)
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE)
    
    # Match scores
    overall_score = models.FloatField(default=0.0)
    skills_score = models.FloatField(default=0.0)
    experience_score = models.FloatField(default=0.0)
    education_score = models.FloatField(default=0.0)
    
    # Match details
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    skill_gap_analysis = models.JSONField(default=dict)
    
    # Processing info
    processing_time_ms = models.IntegerField(default=0)
    algorithm_version = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['resume', 'job']
        ordering = ['-overall_score']
    
    def __str__(self):
        return f"Match: {self.resume.title} -> {self.job.title} ({self.overall_score}%)"


class RecommendationLog(models.Model):
    """Log recommendation system activity"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume = models.ForeignKey('resumes.Resume', on_delete=models.CASCADE)
    
    # Recommendation context
    recommendation_type = models.CharField(max_length=20)  # 'jobs', 'skills', 'courses'
    recommendations = models.JSONField(default=list)
    user_interactions = models.JSONField(default=dict)  # clicks, views, applications
    
    # Performance metrics
    precision_at_k = models.FloatField(blank=True, null=True)
    recall_at_k = models.FloatField(blank=True, null=True)
    diversity_score = models.FloatField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recommendations for {self.user.email}"


class UpskillingSuggestion(models.Model):
    """Store upskilling suggestions based on skill gaps"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upskilling_suggestions')
    skill_name = models.CharField(max_length=100)
    current_level = models.CharField(max_length=20)  # 'none', 'beginner', 'intermediate', 'advanced'
    target_level = models.CharField(max_length=20)
    
    # Suggestion details
    learning_resources = models.JSONField(default=list)  # courses, tutorials, books
    estimated_time_hours = models.IntegerField(default=0)
    difficulty_level = models.CharField(max_length=20, default='intermediate')
    
    # Priority and relevance
    priority_score = models.FloatField(default=0.0)
    market_demand_score = models.FloatField(default=0.0)
    salary_impact_score = models.FloatField(default=0.0)
    
    # Status
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority_score']
        unique_together = ['user', 'skill_name']
    
    def __str__(self):
        return f"Upskilling: {self.skill_name} for {self.user.email}"


class ModelTrainingLog(models.Model):
    """Log model training activities"""
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='training_logs')
    
    # Training parameters
    training_data_size = models.IntegerField(default=0)
    validation_data_size = models.IntegerField(default=0)
    test_data_size = models.IntegerField(default=0)
    
    # Training configuration
    hyperparameters = models.JSONField(default=dict)
    training_algorithm = models.CharField(max_length=100)
    
    # Training metrics
    training_loss = models.FloatField(blank=True, null=True)
    validation_loss = models.FloatField(blank=True, null=True)
    training_time_minutes = models.IntegerField(default=0)
    
    # Results
    final_accuracy = models.FloatField(blank=True, null=True)
    final_precision = models.FloatField(blank=True, null=True)
    final_recall = models.FloatField(blank=True, null=True)
    final_f1_score = models.FloatField(blank=True, null=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('started', 'Started'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='started'
    )
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Training log for {self.model.name}"
