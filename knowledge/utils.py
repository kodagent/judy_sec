import boto3
from django.conf import settings


def list_s3_folders(bucket_name, prefix):
    """
    Lists all folders under a specified prefix in an S3 bucket.
    
    :param bucket_name: Name of the S3 bucket.
    :param prefix: Prefix path to list the folders from.
    """
    # Initialize a boto3 S3 client
    s3_client = boto3.client('s3')

    s3_dirs = []

    # Ensure the prefix ends with a slash
    if not prefix.endswith('/'):
        prefix += '/'

    # Use a paginator to handle the listing
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/')

    print(f"Folders under '{prefix}' in '{bucket_name}':")
    for page in page_iterator:
        # CommonPrefixes contains the "folders" under the current prefix
        for obj in page.get('CommonPrefixes', []):
            print(obj['Prefix'])
            # s3_dirs.append(obj['Prefix'])
    
    # return s3_dirs


# Example usage:
bucket_name = settings.AWS_STORAGE_BUCKET_NAME  # Replace with your actual bucket name
prefix = 'media/scraped_data/'  # Replace with your actual prefix
list_s3_folders(bucket_name, prefix)