from rest_framework import serializers

from meeting.models import (Analysis, CandidateFeedback, InterviewTranscript,
                            RecruiterFeedback)


class InterviewTranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewTranscript
        fields = '__all__'


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = '__all__'


class CandidateFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateFeedback
        fields = '__all__'


class RecruiterFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruiterFeedback
        fields = '__all__'
