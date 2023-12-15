from django.db import models


class OpenAIFile(models.Model):
    title = models.CharField(max_length=255)
    file_id = models.CharField(max_length=255, unique=True)  # ID from OpenAI
    version = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_versions')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (Version {self.version})"

    def save(self, *args, **kwargs):
        if not self.pk:
            # For a new file, no version increment
            super().save(*args, **kwargs)
        else:
            # For an existing file, increment the version and keep a reference to the previous version
            self.version += 1
            previous_version = OpenAIFile.objects.get(pk=self.pk)
            self.previous_version = previous_version
            self.pk = None  # This will create a new record
            super().save(*args, **kwargs)
