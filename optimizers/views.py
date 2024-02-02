import json

from django.http import JsonResponse
from django.views import View
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from optimizers.cl_opt import improve_cover_letter, optimize_cover_letter
from optimizers.job_post import optimize_job_post
from optimizers.models import CoverLetter, JobPost, OptimizedResumeContent, Resume
from optimizers.resume_opt import (
    customize_improved_resume,
    customize_optimized_resume,
    improve_resume,
    optimize_resume,
)

# from optimizers.resume import run_resume_optimization
from optimizers.serializers import (
    CoverLetterSerializer,
    JobPostSerializer,
    ResumeSerializer,
)


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


class ResumeImprovementView(View):
    """
    This view handles resume improvement. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """

    serializer_class = None

    async def get(self, request, applicant_id, format=None):
        try:
            # Get the optimized content
            pdf_url = await improve_resume(applicant_id)
            data = {
                "success": "Improvement complete",
                "improved_content": pdf_url,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class ResumeOptimizationView(View):
    """
    This view handles resume optimization. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """

    serializer_class = None

    async def get(self, request, applicant_id, job_post_id, format=None):
        try:
            # Get the optimized content
            return_data = await optimize_resume(applicant_id, job_post_id)
            data = {
                "success": "Optimization complete",
                "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class ResumeImprovementCustomizationView(View):
    """
    This view handles resume optimization. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """

    serializer_class = None

    async def post(self, request, applicant_id, format=None):
        try:
            # Parse JSON data from the request body
            body_unicode = request.body.decode("utf-8")
            body_data = json.loads(body_unicode)

            # Extract custom_instruction from the parsed data
            custom_instruction = body_data.get("custom_instruction")

            # Call the utility function with applicant_id and custom_instruction
            return_data = await customize_improved_resume(
                applicant_id, custom_instruction
            )
            data = {
                "success": "Optimization complete",
                "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class ResumeOptimizationCustomizationView(View):
    """
    This view handles resume optimization. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """

    serializer_class = None

    async def post(self, request, applicant_id, job_post_id, format=None):
        try:
            # Parse JSON data from the request body
            body_unicode = request.body.decode("utf-8")
            body_data = json.loads(body_unicode)

            # Extract custom_instruction from the parsed data
            custom_instruction = body_data.get("custom_instruction")

            # Call the utility function with applicant_id, job_post_id, and custom_instruction
            return_data = await customize_optimized_resume(
                applicant_id, job_post_id, custom_instruction
            )
            data = {
                "success": "Optimization complete",
                "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class CoverLetterImprovementView(View):
    """
    This view handles cover letter improvement. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """

    serializer_class = None

    async def get(self, request, applicant_id, format=None):
        try:
            # Get the optimized content
            pdf_url = await improve_cover_letter(applicant_id)
            data = {
                "success": "Improvement complete",
                "improved_content": pdf_url,
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
    async def get(self, request, applicant_id, job_post_id, format=None):
        try:
            # Get the optimized content
            # return_data = run_cover_letter_optimization(application_id, job_post_id)
            return_data = await optimize_cover_letter(applicant_id, job_post_id)
            data = {
                "success": "Optimization complete",
                "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class JobOptimizationView(View):
    """
    This view handles job post optimization. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """

    serializer_class = None

    async def get(self, request, job_id, format=None):
        # feedback_only = request.query_params.get("feedback", "false").lower() == "true"
        try:
            optimized_job_post_content = await optimize_job_post(job_id)
            # might need to use the mark down dangerous html before pushing to frontend
            return JsonResponse(
                {
                    "success": "Optimization complete",
                    "optimized_content": optimized_job_post_content,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# http://127.0.0.1:8000/api/optimizers/optimize-job-post/654194177b7c7c8236e8541f/
# http://127.0.0.1:8000/api/optimizers/optimize-job-post/654194177b7c7c8236e8541f/?feedback=true
# http://127.0.0.1:8000/api/optimizers/optimize-resume/63a6af57677ed8a015025a62/654194177b7c7c8236e8541f/
# applicant_id 63a6af57677ed8a015025a62
# job_post_id 654194177b7c7c8236e8541f
# job_post_id = 65aa68567bd03fff776fbfcf
