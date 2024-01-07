import asyncio

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from rest_framework import status

from chatbackend.logging_config import configure_logger
from knowledge.scraper.scrape_scripts.british import scrape_british_site
from knowledge.scraper.scrape_scripts.ontario import scrape_ontario_site
from knowledge.scraper.scraper_utils import clear_s3_directory

logger = configure_logger(__name__)

class ScrapeAndUpdateAPI(View): 
    async def get(self, request, *args, **kwargs):
        try:
            # Clear the scraped_data directory first
            clear_s3_directory(settings.AWS_STORAGE_BUCKET_NAME, 'media/scraped_data')

            # Create tasks for both scraping functions
            task1 = asyncio.create_task(scrape_ontario_site())
            task2 = asyncio.create_task(scrape_british_site())

            # Wait for both tasks to complete
            await asyncio.gather(task1, task2)

            return JsonResponse({'status': 'success', 'message': 'Scraping initiated'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 