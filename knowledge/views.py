from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from rest_framework import status

from assistant.engine import OpenAIChatEngine
from chatbackend.logging_config import configure_logger
from knowledge.models import OpenAIFile
from knowledge.scraper.scrape_scripts.ontario import scrape_ontario_site

logger = configure_logger(__name__)

class ScrapeAndUpdateAPI(View):
    async def get(self, request, *args, **kwargs):
        website = "ontario"
        output_file_path = f"knowledge/scraper/scraped_data/scraped_{website}_content.txt"

        # # Run scraping
        # if website == "ontario":
        #     await scrape_ontario_site()

        # Initialize OpenAI client
        assistant_id = settings.ASSISTANT_ID
        openai_client = OpenAIChatEngine(api_key=settings.OPENAI_API_KEY, assistant_id=assistant_id)

        # Handle file update or creation
        try:
            new_file_id = await self.handle_file_update_or_creation(website, output_file_path, openai_client, assistant_id)
            await openai_client.attach_file_to_assistant(assistant_id, file_id=new_file_id)
            logger.info(f"File ID update: {new_file_id}")
            return JsonResponse({"message": "Scraping and uploading completed."}, status=status.HTTP_200_OK)
        except Exception as e:
            # Handle other exceptions
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def handle_file_update_or_creation(self, website, output_file_path, openai_client, assistant_id):
        new_file = await openai_client.upload_file(output_file_path)
        logger.info(f"This is the new file: {new_file}")
        try:
            existing_file = await sync_to_async(OpenAIFile.objects.get, thread_sensitive=True)(title=website)
            if existing_file:
                logger.info(f"Deleting...: {existing_file.file_id}")  
                await openai_client.delete_file(file_id=existing_file.file_id, assistant_id=assistant_id)
                existing_file.file_id = new_file.id
                await sync_to_async(existing_file.save, thread_sensitive=True)()
        except Exception as e:
            await sync_to_async(OpenAIFile.objects.create, thread_sensitive=True)(title=website, file_id=new_file.id)
    
        return new_file.id