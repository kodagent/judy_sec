import os

from django.core.validators import FileExtensionValidator
from django.db import models
from google.cloud import storage

from accounts.models import User


class UploadManager(models.Manager):
    def latest_upload_by_user(self, user):
        return self.filter(user=user).order_by('-upload_time').first()


class Upload(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='files/', validators=[FileExtensionValidator(['pdf', 'docx', 'doc', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7zip'])])
    updated_date = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    upload_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)

    objects = UploadManager()

    def __str__(self):
        return f"{self.user.first_name}: {self.title}"

    def get_extension_short(self):
        ext = str(self.file).split(".")
        ext = ext[len(ext)-1]

        if ext == 'doc' or ext == 'docx':
            return 'word'
        elif ext == 'pdf':
            return 'pdf'
        elif ext == 'xls' or ext == 'xlsx':
            return 'excel'
        elif ext == 'ppt' or ext == 'pptx':
            return 'powerpoint'
        elif ext == 'zip' or ext == 'rar' or ext == '7zip':
            return 'archive'
    
    # def save(self, *args, **kwargs):
    #     if self.get_extension_short() == 'word':
    #         # self.file = convert_file(self.file, self.title)
    #         # pdf_content = convert_file(self.file, self.title)
    #         # self.file.save(f"{self.title}.pdf", ContentFile(pdf_content))
    #         self.merged_file = merge_word_documents(self.user_id, self.file)
    #     super().save(*args, **kwargs)

    # def delete(self, *args, **kwargs):
    #     self.file.delete()
    #     super().delete(*args, **kwargs)
    
    # include this code when it is to be connected to GCP
    def delete(self, *args, **kwargs):
        # Delete the file from Google Cloud Storage
        if self.file.name:
            # Create a storage client
            storage_client = storage.Client()

            # Specify the bucket name
            bucket_name = os.getenv("GS_BUCKET_NAME")

            # Get the bucket
            bucket = storage_client.get_bucket(bucket_name)

            # Get the file name in GCS
            file_name = os.path.basename(self.file.name)

            # Create a blob object pointing to the file in the bucket
            blob = bucket.blob(file_name)

            # Check if the file exists in the bucket before deleting
            if blob.exists():
                # Delete the file from Google Cloud Storage
                blob.delete()

        # Delete the associated file from Django's default storage
        self.file.delete()
        
        # Delete the database record
        super().delete(*args, **kwargs)