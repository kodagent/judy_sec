from django.urls import path

from meeting import views

urlpatterns = [
    path('transcript-analysis/', views.TranscriptAnalysis.as_view(), name='transcript_analysis'),
]
