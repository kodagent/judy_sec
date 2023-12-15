from django.urls import path
from record import views

urlpatterns = [
    path('knowledge/', views.FileView.as_view(), name='file_view'),
    path('upload/', views.FileUploadView.as_view(), name='file_upload'),
    path('update/<int:pk>/', views.UploadUpdateView.as_view(), name='file_update'),
    path('delete/<int:pk>/', views.UploadDeleteView.as_view(), name='file_delete'),
]

