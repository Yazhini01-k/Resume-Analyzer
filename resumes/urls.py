from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.ResumeUploadView.as_view(), name='resume-upload'),
    path('', views.ResumeListView.as_view(), name='resume-list'),
    path('<int:pk>/', views.ResumeDetailView.as_view(), name='resume-detail'),
    path('<int:resume_id>/analysis/', views.resume_analysis, name='resume-analysis'),
    path('<int:resume_id>/reprocess/', views.reprocess_resume, name='reprocess-resume'),
    path('skill-profile/', views.SkillProfileView.as_view(), name='skill-profile'),
]
