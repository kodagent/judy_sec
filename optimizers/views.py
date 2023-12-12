from django.http import JsonResponse
from django.views import View
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from optimizers.cl_opt import run_cover_letter_optimization
from optimizers.job_post import run_job_post_optimization
from optimizers.models import (CoverLetter, JobPost, OptimizedContent,
                               OptimizedResume, Resume)
from optimizers.resume import run_resume_optimization
from optimizers.serializers import (CoverLetterSerializer, JobPostSerializer,
                                    ResumeSerializer)


class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer

    # This method will handle the default behavior of the GET request for a specific resume
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer

    # This method will handle the default behavior of the GET request for a specific JobPost
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CoverLetterViewSet(viewsets.ModelViewSet):
    queryset = CoverLetter.objects.all()
    serializer_class = CoverLetterSerializer

    # This method will handle the default behavior of the GET request for a specific CoverLetter
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ResumeOptimizationView(View):
    """
    This view handles resume optimization. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """
    serializer_class = None

    # def get(self, request, application_id, job_post_id, format=None):
    async def get(self, request, application_id, job_post_id, format=None):
        try:
            # Get the optimized content
            # return_data = run_resume_optimization(application_id, job_post_id)
            return_data = await run_resume_optimization(application_id, job_post_id)
            data = {
                "success": "Optimization complete",
                "optimized_content": return_data
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class CoverLetterOptimizationView(View):
    """
    This view handles cover letter optimization. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """
    serializer_class = None

    # def get(self, request, application_id, job_post_id, format=None):
    async def get(self, request, application_id, job_post_id, format=None):
        try:
            # Get the optimized content
            # return_data = run_cover_letter_optimization(application_id, job_post_id)
            return_data = await run_cover_letter_optimization(application_id, job_post_id)
            data = {
                "success": "Optimization complete",
                "optimized_content": return_data
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class JobOptimizationView(APIView):
    """
    This view handles job post optimization. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """
    serializer_class = None

    def get(self, request, job_id, format=None):
        feedback_only = request.query_params.get('feedback', 'false').lower() == 'true'

        try:
            if feedback_only:
                # Get only the feedback
                content_feedback = run_job_post_optimization(job_id, feedback=True)
                return Response({
                    "success": "Feedback retrieval complete",
                    "post_feedback": content_feedback
                })
            else:
                # Get the optimized content
                optimized_job_post_content = run_job_post_optimization(job_id)
                return Response({
                    "success": "Optimization complete",
                    "optimized_content": optimized_job_post_content
                })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# http://127.0.0.1:8000/api/optimizers/optimize-job-post/654194177b7c7c8236e8541f/
# http://127.0.0.1:8000/api/optimizers/optimize-job-post/654194177b7c7c8236e8541f/?feedback=true
# http://127.0.0.1:8000/api/optimizers/optimize-resume/63a6af57677ed8a015025a62/654194177b7c7c8236e8541f/
# applicant_id 63a6af57677ed8a015025a62
# job_post_id 654194177b7c7c8236e8541f