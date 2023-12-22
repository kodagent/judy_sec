from django.urls import path

from recommendation import views

urlpatterns = [
    path('create-matrix/', views.CreateMatrixView.as_view(), name='create_matrix'),
    path('jobs/<str:candidate_id>/', views.JobRecommendationView.as_view(), name='job_recommendations'),
    path('candidates/<str:job_id>/', views.CandidateRecommendationView.as_view(), name='candidate_recommendations'),
]
