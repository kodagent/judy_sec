import asyncio

from django.conf import settings
from django.http import JsonResponse
from django.views import View
from rest_framework import status

from chatbackend.configs.logging_config import configure_logger
from knowledge.knowledge_vec import query_vec_database, save_vec_to_database
from knowledge.scraper.scrape_scripts.alberta_1 import scrape_alberta_site_1
from knowledge.scraper.scrape_scripts.alberta_2 import scrape_alberta_site_2
from knowledge.scraper.scrape_scripts.alberta_3 import scrape_alberta_site_3
from knowledge.scraper.scrape_scripts.british import scrape_british_site
from knowledge.scraper.scrape_scripts.ontario import scrape_ontario_site
from knowledge.scraper.scraper_utils import clear_s3_directory

logger = configure_logger(__name__)

class ScrapeAndUpdateAPI(View): 
    async def get(self, request, *args, **kwargs):
        try:
            clear_s3_directory(settings.AWS_STORAGE_BUCKET_NAME, 'media/scraped_data')
            tasks = [
                asyncio.create_task(scrape_ontario_site()),
                asyncio.create_task(scrape_british_site()),
                asyncio.create_task(scrape_alberta_site_1()),
                asyncio.create_task(scrape_alberta_site_2()),
                asyncio.create_task(scrape_alberta_site_3()),
            ]
            await asyncio.gather(*tasks)
            return JsonResponse({'status': 'success', 'message': 'Scraping initiated'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SaveVecToDBAPI(View):
    async def get(self, request, *args, **kwargs):
        try:
            # Convert the asynchronous function to synchronous for Django compatibility
            await save_vec_to_database()
            return JsonResponse({"Success": "Done saving vector to vecDB"}, status=200)
        except Exception as e:
            # Log the error and send an error response
            logger.error(f"Error in SaveVecToDBAPI: {e}")
            return JsonResponse({"Error": "Failed to save vector to vecDB"}, status=500)


class QueryVecDBAPI(View):
    async def get(self, request, *args, **kwargs):
        try:
            # Convert the asynchronous function to synchronous for Django compatibility
            await query_vec_database(query="What is the BCCNM's legal obligation?", num_results=4)
            return JsonResponse({"Success": "Answer contexts received"}, status=200)
        except Exception as e:
            # Log the error and send an error response
            logger.error(f"Error in QueryVecDBAPI: {e}")
            return JsonResponse({"Error": "Context collection failed"}, status=500)