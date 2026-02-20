from django.urls import path
from . import views

urlpatterns = [
    path('extract-skills/', views.extract_skills, name='extract-skills'),
    path('calculate-match/', views.calculate_job_match, name='calculate-job-match'),
    path('recommendations/', views.get_recommendations, name='get-recommendations'),
    path('recommended-jobs/', views.recommended_jobs, name='recommended-jobs'),
    # Temporarily disabled due to missing table
    # path('upskilling/', views.UpskillingSuggestionListView.as_view(), name='upskilling-suggestions'),
    # path('upskilling/<int:suggestion_id>/complete/', views.mark_suggestion_completed, name='mark-suggestion-completed'),
    path('analytics/', views.ml_analytics, name='ml-analytics'),
    path('models/', views.MLModelListView.as_view(), name='ml-models'),
    path('training-logs/', views.ModelTrainingLogListView.as_view(), name='training-logs'),
]
