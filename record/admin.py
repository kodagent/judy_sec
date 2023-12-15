from django.contrib import admin
from record.models import Upload


class UploadAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "updated_date", "upload_time", "get_extension_short"]

    def get_extension_short(self, obj):
        return obj.get_extension_short()

    get_extension_short.short_description = "File Type"


# Register your models here.
admin.site.register(Upload, UploadAdmin)
