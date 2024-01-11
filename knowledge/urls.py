from django.urls import path

from knowledge.views import QueryVecDBAPI, SaveVecToDBAPI, ScrapeAndUpdateAPI

urlpatterns = [
    path('scrape-update/<str:scraper_province>/', ScrapeAndUpdateAPI.as_view(), name='scrape_update_api'),
    path('save-vec-to-db/<str:province_dir>/', SaveVecToDBAPI.as_view(), name='save_vec_to_db'),
    path('query-vec-db/', QueryVecDBAPI.as_view(), name='query_vec_db'),
]

# review:
# crns, alberta_2, alberta_3