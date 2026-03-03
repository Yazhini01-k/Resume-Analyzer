from django.urls import path
from . import views
from . import recommendation_views

urlpatterns = [
    path('', views.JobListView.as_view(), name='job-list'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('create/', views.JobCreateView.as_view(), name='job-create'),
    path('<int:pk>/update/', views.JobUpdateView.as_view(), name='job-update'),
    path('<int:pk>/delete/', views.JobDeleteView.as_view(), name='job-delete'),
    path('my-posted/', views.my_posted_jobs, name='my-posted-jobs'),
    path('<int:job_id>/rank-candidates/', views.rank_candidates_for_job, name='rank-candidates'),
    path('categories/', views.JobCategoryListView.as_view(), name='job-categories'),
    path('skills/', views.JobSkillListView.as_view(), name='job-skills'),
    path('my-skills/', views.my_skills_summary, name='my-skills'),
    
    # Dynamic Recommendation API Endpoints
    path('dynamic-recommendations/', recommendation_views.get_dynamic_recommendations, name='dynamic-recommendations'),
    path('refresh-recommendations/', recommendation_views.refresh_recommendations, name='refresh-recommendations'),
    path('recommendation/<int:match_id>/viewed/', recommendation_views.mark_recommendation_viewed, name='mark-recommendation-viewed'),
    path('recommendation/<int:match_id>/save/', recommendation_views.save_recommendation, name='save-recommendation'),
    path('recommendation-analytics/', recommendation_views.get_recommendation_analytics, name='recommendation-analytics'),
    path('skill-analysis/', recommendation_views.get_skill_analysis, name='skill-analysis'),
    path('job-market-insights/', recommendation_views.get_job_market_insights, name='job-market-insights'),
    path('search-by-skills/', recommendation_views.search_jobs_by_skills, name='search-jobs-by-skills'),
]
