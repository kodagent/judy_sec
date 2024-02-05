from django.urls import include, path
from rest_framework.routers import DefaultRouter

from optimizers import views
from optimizers.views import (
    CoverLetterViewSet,
    JobPostViewSet,
    OptimizedCoverLetterContentViewSet,
    OptimizedResumeContentViewSet,
    ResumeViewSet,
)

router = DefaultRouter()
router.register(r"improved_resumes", ResumeViewSet)
router.register(r"optimized_resumes", OptimizedResumeContentViewSet)
router.register(r"improved_cover_letters", CoverLetterViewSet)
router.register(r"optimized_cover_letters", OptimizedCoverLetterContentViewSet)
router.register(r"job_posts", JobPostViewSet)


urlpatterns = [
    path("", include(router.urls)),
    # =====================> Resume URLs <=====================
    path(
        "improve-resume/<str:applicant_id>/",
        views.ResumeImprovementView.as_view(),
        name="improve_resume",
    ),  # ~ 173 secs
    path(
        "optimize-resume/<str:applicant_id>/<str:job_post_id>/",
        views.ResumeOptimizationView.as_view(),
        name="resume_optimization",
    ),  # ~ 91 secs
    path(
        "customize-improved-resume/<str:applicant_id>/",
        views.ResumeImprovementCustomizationView.as_view(),
        name="customize_improved_resume",
    ),  # ~ 92 secs
    path(
        "customize-optimize-resume/<str:applicant_id>/<str:job_post_id>/",
        views.ResumeOptimizationCustomizationView.as_view(),
        name="customize_resume_optimization",
    ),  # ~ 80 secs
    # =====================> Cover Letter URLs <=====================
    path(
        "create-cover-letter/<str:applicant_id>/",
        views.CoverLetterCreationView.as_view(),
        name="create_cover_letter",
    ),
    path(
        "improve-cover-letter/<str:applicant_id>/",
        views.CoverLetterImprovementView.as_view(),
        name="improve_cover_letter",
    ),  # ~ 58 secs
    path(
        "optimize-cover-letter/<str:applicant_id>/<str:job_post_id>/",
        views.CoverLetterOptimizationView.as_view(),
        name="optimize_cover_letter",
    ),  # ~ 41 secs
    path(
        "customize-improved-cover-letter/<str:applicant_id>/",
        views.CoverLetterImprovementCustomizationView.as_view(),
        name="customize_improved_cover_letter",
    ),  # ~ 53 secs
    path(
        "customize-optimize-cover-letter/<str:applicant_id>/<str:job_post_id>/",
        views.CoverLetterOptimizationCustomizationView.as_view(),
        name="customize_cover_letter_optimization",
    ),  # ~ 50 secs
    # =====================> Job Post URLs <=====================
    path(
        "optimize-job-post/<str:job_id>/",
        views.JobOptimizationView.as_view(),
        name="job_post_optimization",
    ),
]
