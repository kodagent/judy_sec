from django.contrib import admin

from meeting.models import (Analysis, CandidateFeedback, InterviewTranscript,
                            RecruiterFeedback)


class InterviewTranscriptAdmin(admin.ModelAdmin):
    list_display = ['transcript_id', 'candidate_name', 'interview_date']


class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['analysis_type', 'result']


class CandidateFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'feedback',
    ]


class RecruiterFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'feedback',
    ]


admin.site.register(InterviewTranscript, InterviewTranscriptAdmin)
admin.site.register(Analysis, AnalysisAdmin)
admin.site.register(CandidateFeedback, CandidateFeedbackAdmin)
admin.site.register(RecruiterFeedback, RecruiterFeedbackAdmin)
