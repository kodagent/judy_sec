from django.contrib import admin

from .models import (
    CoverLetter,
    CoverLetterAnalysis,
    JobPost,
    JobPostAnalysis,
    OptimizedCoverLetterContent,
    OptimizedJobPostContent,
    OptimizedResume,
    Resume,
    ResumeAnalysis,
)


# JobPost
class JobPostAnalysisInline(admin.TabularInline):
    model = JobPostAnalysis
    extra = 0


class JobPostAdmin(admin.ModelAdmin):
    list_display = ("job_post_id", "title", "posted_at")
    search_fields = ("job_post_id", "title")
    ordering = ("-posted_at",)
    inlines = [JobPostAnalysisInline]


# CoverLetter
class CoverLetterAnalysisInline(admin.TabularInline):
    model = CoverLetterAnalysis
    extra = 0


class CoverLetterAdmin(admin.ModelAdmin):
    list_display = ("cover_letter_id", "display_original_pdf", "display_improved_pdf")
    search_fields = ("cover_letter_id",)

    def display_original_pdf(self, obj):
        return obj.original_pdf.url if obj.original_pdf else "No File"

    display_original_pdf.short_description = "Original PDF"

    def display_improved_pdf(self, obj):
        return obj.general_improved_pdf.url if obj.general_improved_pdf else "No File"

    display_improved_pdf.short_description = "Improved PDF"
    inlines = [CoverLetterAnalysisInline]


# Resume
class ResumeAnalysisInline(admin.TabularInline):
    model = ResumeAnalysis
    extra = 0


class ResumeAdmin(admin.ModelAdmin):
    list_display = ("resume_id", "display_original_pdf", "display_improved_pdf")
    search_fields = ("resume_id",)

    def display_original_pdf(self, obj):
        return obj.original_pdf.url if obj.original_pdf else "No File"

    display_original_pdf.short_description = "Original PDF"

    def display_improved_pdf(self, obj):
        return obj.general_improved_pdf.url if obj.general_improved_pdf else "No File"

    display_improved_pdf.short_description = "Improved PDF"
    inlines = [ResumeAnalysisInline]


# Register your models here
admin.site.register(JobPost, JobPostAdmin)
admin.site.register(OptimizedJobPostContent)
admin.site.register(CoverLetter, CoverLetterAdmin)
admin.site.register(OptimizedCoverLetterContent)
admin.site.register(Resume, ResumeAdmin)
admin.site.register(OptimizedResume)
