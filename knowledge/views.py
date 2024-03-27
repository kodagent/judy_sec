import asyncio
import time

from chatbackend.configs.logging_config import configure_logger
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from knowledge.knowledge_vec import (
    query_vec_database,
    save_vec_to_database,
    save_vec_to_database_task,
)
from knowledge.scraper.scrape_scripts.alberta_1 import scrape_alberta_site_1
from knowledge.scraper.scrape_scripts.alberta_2 import scrape_alberta_site_2
from knowledge.scraper.scrape_scripts.alberta_3 import scrape_alberta_site_3
from knowledge.scraper.scrape_scripts.british import scrape_british_site
from knowledge.scraper.scrape_scripts.brunswick_1 import (
    scrape_nanb_site,
    scrape_nanb_site_task,
)
from knowledge.scraper.scrape_scripts.brunswick_2 import (
    scrape_anblpn_site,
    scrape_anblpn_site_task,
)
from knowledge.scraper.scrape_scripts.manitoba_1 import (
    scrape_crnm_site,
    scrape_crnm_site_task,
)
from knowledge.scraper.scrape_scripts.manitoba_2 import (
    scrape_clpnm_site,
    scrape_clpnm_site_task,
)
from knowledge.scraper.scrape_scripts.manitoba_3 import (
    scrape_crpnm_site,
    scrape_crpnm_site_task,
)
from knowledge.scraper.scrape_scripts.ontario import scrape_ontario_site
from knowledge.scraper.scrape_scripts.saskatchewan_1 import scrape_crns_site
from knowledge.scraper.scrape_scripts.saskatchewan_2 import (
    scrape_clpns_site,
    scrape_clpns_site_task,
)
from knowledge.scraper.scrape_scripts.saskatchewan_3 import scrape_rpnas_site
from knowledge.scraper.scraper_utils import clear_s3_directory
from rest_framework import status

logger = configure_logger(__name__)


class ScrapeAndUpdateAPI(View):
    async def get(self, request, scraper_province, *args, **kwargs):
        try:
            scrapers = {
                "ontario": scrape_ontario_site,
                "british": scrape_british_site,
                "alberta_1": scrape_alberta_site_1,
                "alberta_2": scrape_alberta_site_2,
                "alberta_3": scrape_alberta_site_3,  # worked on this
                "saskatchewan_1": scrape_crns_site,
                "saskatchewan_2": scrape_clpns_site,  # worked on this
                "saskatchewan_3": scrape_rpnas_site,
                "manitoba_1": scrape_crnm_site,
                "manitoba_2": scrape_clpnm_site,
                "manitoba_3": scrape_crpnm_site,
                "brunswick_1": scrape_nanb_site,
                "brunswick_2": scrape_anblpn_site,
                # background tasks
                "saskatchewan_2_celery": scrape_clpns_site_task,
                "manitoba_1_celery": scrape_crnm_site_task,
                "manitoba_2_celery": scrape_clpnm_site_task,
                "manitoba_3_celery": scrape_crpnm_site_task,
                "brunswick_1_celery": scrape_nanb_site_task,
                "brunswick_2_celery": scrape_anblpn_site_task,
            }

            if scraper_province in scrapers:
                # To delete both pdfs and scraped content dir
                clear_s3_directory(
                    settings.AWS_STORAGE_BUCKET_NAME,
                    f"media/scraped_data/{scraper_province}/",
                )

                start_time = time.time()
                # await scrapers[scraper_province]()
                scrapers[scraper_province].delay()
                duration = time.time() - start_time
                logger.info(f"SCRAPING DURATION: {duration:.2f} seconds")

                return JsonResponse(
                    {
                        "status": "success",
                        "message": f"Scraping {scraper_province} initiated",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return JsonResponse(
                    {"status": "error", "message": "Invalid scraper key"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return JsonResponse(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SaveVecToDBAPI(View):
    async def get(self, request, province_dir, *args, **kwargs):
        try:
            # Convert the asynchronous function to synchronous for Django compatibility
            await save_vec_to_database(province_dir, first_db_opt=True)
            # save_vec_to_database_task.delay(province_dir, first_db_opt=True)

            return JsonResponse({"Success": "Done saving vector to vecDB"}, status=200)
        except Exception as e:
            # Log the error and send an error response
            logger.error(f"Error in SaveVecToDBAPI: {e}")
            return JsonResponse({"Error": "Failed to save vector to vecDB"}, status=500)


class QueryVecDBAPI(View):
    async def get(self, request, *args, **kwargs):
        try:
            # Convert the asynchronous function to synchronous for Django compatibility
            await query_vec_database(
                query="What is the BCCNM's legal obligation?", num_results=3
            )
            return JsonResponse({"Success": "Answer contexts received"}, status=200)
        except Exception as e:
            # Log the error and send an error response
            logger.error(f"Error in QueryVecDBAPI: {e}")
            return JsonResponse({"Error": "Context collection failed"}, status=500)
