from django.contrib import admin

from recommendation import models


class UserSimilarityMatrix(admin.ModelAdmin):
    list_display = ['date_created']


admin.site.register(models.SimilarityMatrix, UserSimilarityMatrix)