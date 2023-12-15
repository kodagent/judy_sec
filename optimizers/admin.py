from django.contrib import admin

from optimizers.models import (Analysis, CoverLetter, JobPost,
                               OptimizedContent, OptimizedResume, Resume,
                               ResumeAnalysis)


class JobPostAdmin(admin.ModelAdmin):
    list_display = ['job_post_id', 'title', 'description', 'posted_at']


class CoverLetterAdmin(admin.ModelAdmin):
    list_display = ['cover_letter_id', 'content', 'job_post', 'submitted_at']


class AnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'cover_letter', 'job_post', 'keyword_matches', 'readability_score',
        'sentiment_score', 'tone_analysis', 'analyzed_at',
    ]


class OptimizedContentAdmin(admin.ModelAdmin):
    list_display = [
        'original_cover_letter', 'original_job_post', 'optimized_content', 'analysis', 
        'optimized_at',
    ]


class ResumeAdmin(admin.ModelAdmin):
    list_display = [
        'resume_id', 'content', 'job_post', 'submitted_at',
    ]


class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'resume', 'keyword_matches', 'complexity_score', 'readability_score',
        'section_feedback', 'analyzed_at',
    ]


class OptimizedResumeAdmin(admin.ModelAdmin):
    list_display = [
        'original_resume', 'optimized_content', 'analysis', 'optimized_at',
    ]


admin.site.register(JobPost, JobPostAdmin)
admin.site.register(CoverLetter, CoverLetterAdmin)
admin.site.register(Analysis, AnalysisAdmin)
admin.site.register(OptimizedContent, OptimizedContentAdmin)
admin.site.register(Resume, ResumeAdmin)
admin.site.register(ResumeAnalysis, ResumeAnalysisAdmin)
admin.site.register(OptimizedResume, OptimizedResumeAdmin)
