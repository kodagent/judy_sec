from django.contrib import admin

from knowledge.models import OpenAIFile


class OpenAIFileAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'file_id', 'version', 'previous_version',
        'uploaded_at', 'updated_at',
    ]

admin.site.register(OpenAIFile, OpenAIFileAdmin)