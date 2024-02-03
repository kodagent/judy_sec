from rest_framework import serializers

from .models import (
    CoverLetter,
    CoverLetterAnalysis,
    JobPost,
    JobPostAnalysis,
    OptimizedCoverLetterContent,
    OptimizedResumeContent,
    Resume,
    ResumeAnalysis,
)


class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = "__all__"


# CoverLetter
class CoverLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = "__all__"


class CoverLetterAnalysisSerializer(serializers.ModelSerializer):
    cover_letter = CoverLetterSerializer(read_only=True)

    class Meta:
        model = CoverLetterAnalysis
        fields = "__all__"


class OptimizedCoverLetterContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizedCoverLetterContent
        fields = "__all__"


# Resume
class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = "__all__"


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    resume = ResumeSerializer(read_only=True)

    class Meta:
        model = ResumeAnalysis
        fields = "__all__"


class OptimizedResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizedResumeContent
        fields = "__all__"
