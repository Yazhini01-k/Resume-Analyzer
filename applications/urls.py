from django.urls import path
from . import views

urlpatterns = [
    path('', views.ApplicationListView.as_view(), name='application-list'),
    path('create/', views.ApplicationCreateView.as_view(), name='application-create'),
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
    path('<int:application_id>/status/', views.change_application_status, name='change-application-status'),
    path('<int:application_id>/withdraw/', views.withdraw_application, name='withdraw-application'),
    path('<int:application_id>/documents/', views.ApplicationDocumentListView.as_view(), name='application-documents'),
    path('<int:application_id>/interview/', views.InterviewScheduleView.as_view(), name='interview-schedule'),
    path('<int:application_id>/interview/confirm/', views.confirm_interview, name='confirm-interview'),
    path('<int:application_id>/feedback/', views.ApplicationFeedbackView.as_view(), name='application-feedback'),
    path('statistics/', views.application_statistics, name='application-statistics'),
]
