from django.urls import path

from knowledge.views import ScrapeAndUpdateAPI

urlpatterns = [
    path('scrape-update/', ScrapeAndUpdateAPI.as_view(), name='scrape_update_api'),
]
