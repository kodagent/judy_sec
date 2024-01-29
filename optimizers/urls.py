from django.urls import include, path
from rest_framework.routers import DefaultRouter

from optimizers import views
from optimizers.views import ResumeViewSet  # , RunResumeOptimizationView)
from optimizers.views import CoverLetterViewSet, JobPostViewSet

router = DefaultRouter()
router.register(r"resumes", ResumeViewSet)
router.register(r"job_posts", JobPostViewSet)
router.register(r"cover_letters", CoverLetterViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # path(
    #     "optimize-resume/<str:application_id>/<str:job_post_id>/",
    #     views.ResumeOptimizationView.as_view(),
    #     name="resume_optimization",
    # ),
    path(
        "improve-cover-letter/<str:applicant_id>/",
        views.CoverLetterImprovementView.as_view(),
        name="improve_cover_letter",
    ),
    path(
        "optimize-cover-letter/<str:applicant_id>/<str:job_post_id>/",
        views.CoverLetterOptimizationView.as_view(),
        name="optimize_cover_letter",
    ),
    path(
        "optimize-job-post/<str:job_id>/",
        views.JobOptimizationView.as_view(),
        name="job_post_optimization",
    ),
]
