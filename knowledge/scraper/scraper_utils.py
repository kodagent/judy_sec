import re
from io import BytesIO

import boto3
import requests
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from chatbackend.configs.logging_config import configure_logger

logger = configure_logger(__name__)

# Function to sanitize file names
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '-', name)


# Function to download PDF using Playwright and save to s3
async def download_pdf(url, pdf_name):
    # if settings.DEBUG:
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    #     }
    # else:
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    #     }
    try:
        # Send a GET request to the URL
        response = requests.get(url)  # , headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Prepend 'scraped_data/' to the pdf_name for S3
            s3_pdf_name = f"scraped_data/{pdf_name}"

            # Check if the file exists in S3 and get an available name
            if default_storage.exists(s3_pdf_name):
                # s3_pdf_name = default_storage.get_available_name(s3_pdf_name)
                logger.info(f"PDF {s3_pdf_name} already exists in S3. Skipping download.")
                return False

            # Save the response content to S3
            default_storage.save(s3_pdf_name, ContentFile(BytesIO(response.content).read()))
            logger.info(f"PDF saved to S3 as {s3_pdf_name}")
            return True
        else:
            logger.error(f"Failed to download PDF from {url}: HTTP Status Code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error saving PDF to S3 from {url}: {str(e)}")
        return False


def clear_s3_directory(bucket_name, directory_name):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    directory_name = directory_name.rstrip('/') + '/'  
    try:
        objects_to_delete = []
        for obj in bucket.objects.filter(Prefix=directory_name):
            objects_to_delete.append({'Key': obj.key})

        if objects_to_delete:
            bucket.delete_objects(Delete={'Objects': objects_to_delete})
            for obj in objects_to_delete:
                logger.info(f"Deleted {obj['Key']}...")
        else:
            logger.info("No files found to delete.")

        logger.info("Done with Delete operation on S3 bucket.")
    except Exception as e:
        logger.error(f"Error during deletion: {e}")
