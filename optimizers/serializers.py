from rest_framework import serializers

from optimizers.models import (CoverLetter, JobPost, OptimizedContent,
                               OptimizedResume, Resume)


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = '__all__'


class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = '__all__'


class CoverLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = '__all__'


class OptimizedResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizedResume
        fields = '__all__'


class OptimizedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizedContent
        fields = '__all__'