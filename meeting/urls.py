from django.urls import path

from meeting import views

urlpatterns = [
    path('api/transcript-analysis/', views.TranscriptAnalysis.as_view(), name='transcript_analysis'),
]


# # Data to be sent in the request
# data = {
#     'transcript_id': '123',
#     'transcript': 'Your interview transcript here',
# }