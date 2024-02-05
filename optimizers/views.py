import json

from django.http import JsonResponse
from django.views import View
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from optimizers.cl_opt import (
    customize_improved_cover_letter,
    customize_optimized_cover_letter,
    get_default_cover_letter,
    improve_cover_letter,
    optimize_cover_letter,
)
from optimizers.job_post import optimize_job_post
from optimizers.models import (
    CoverLetter,
    JobPost,
    OptimizedCoverLetterContent,
    OptimizedResumeContent,
    Resume,
)
from optimizers.resume_opt import (
    customize_improved_resume,
    customize_optimized_resume,
    improve_resume,
    optimize_resume,
)
from optimizers.serializers import (
    CoverLetterSerializer,
    JobPostSerializer,
    OptimizedCoverLetterContentSerializer,
    OptimizedResumeSerializer,
    ResumeSerializer,
)


class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    lookup_field = "resume_id"

    # This method will handle the default behavior of the GET request for a specific Resume
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class OptimizedResumeContentViewSet(viewsets.ModelViewSet):
    queryset = OptimizedResumeContent.objects.all()
    serializer_class = OptimizedResumeSerializer
    lookup_field = "resume_id"

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        resume_id = self.kwargs.get("resume_id")
        obj = queryset.filter(resume__resume_id=resume_id).first()
        self.check_object_permissions(self.request, obj)
        return obj

    # This method will handle the default behavior of the GET request for a specific Optimized Resume
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CoverLetterViewSet(viewsets.ModelViewSet):
    queryset = CoverLetter.objects.all()
    serializer_class = CoverLetterSerializer
    lookup_field = "cover_letter_id"

    # This method will handle the default behavior of the GET request for a specific CoverLetter
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class OptimizedCoverLetterContentViewSet(viewsets.ModelViewSet):
    queryset = OptimizedCoverLetterContent.objects.all()
    serializer_class = CoverLetterSerializer
    lookup_field = "cover_letter_id"

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        cover_letter_id = self.kwargs.get("cover_letter_id")
        obj = queryset.filter(cover_letter__cover_letter_id=cover_letter_id).first()
        self.check_object_permissions(self.request, obj)
        return obj

    # This method will handle the default behavior of the GET request for a specific Optimized CoverLetter
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    lookup_field = "job_post_id"

    # This method will handle the default behavior of the GET request for a specific JobPost
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ============================> RESUME <============================
class ResumeImprovementView(View):
    """
    Improves a resume for a given applicant ID
    """

    async def get(self, request, applicant_id, format=None):
        try:
            # Get the optimized content
            pdf_url = improve_resume.delay(applicant_id)
            # pdf_url = await improve_resume(applicant_id)
            data = {
                "success": "Resume Improvement Initiated",
                # "improved_content": pdf_url,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class ResumeOptimizationView(View):
    """
    Improves a resume for a given applicant ID to the given job ID
    """

    serializer_class = None

    async def get(self, request, applicant_id, job_post_id, format=None):
        try:
            # Get the optimized content
            return_data = optimize_resume.delay(applicant_id, job_post_id)
            # return_data = await optimize_resume(applicant_id, job_post_id)
            data = {
                "success": "Resume Optimization Initiated",
                # "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class ResumeImprovementCustomizationView(View):
    """
    Customizes improved resume for a given applicant ID
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
            return_data = customize_improved_resume.delay(
                applicant_id, custom_instruction
            )
            # return_data = await customize_improved_resume(
            #     applicant_id, custom_instruction
            # )
            data = {
                "success": "Resume Improvement Customization Initiated",
                # "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class ResumeOptimizationCustomizationView(View):
    """
    Customizes tailored resume for a given applicant ID to the given job ID
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
            return_data = customize_optimized_resume.delay(
                applicant_id, job_post_id, custom_instruction
            )
            # return_data = await customize_optimized_resume(
            #     applicant_id, job_post_id, custom_instruction
            # )
            data = {
                "success": "Resume Optimization Customization Initiated",
                # "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# ============================> RESUME <============================


# ============================> COVER LETTER <============================
class CoverLetterCreationView(View):
    """
    This view handles cover letter creation. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """

    serializer_class = None

    async def get(self, request, applicant_id, format=None):
        try:
            # Get the optimized content
            pdf_url = get_default_cover_letter.delay(applicant_id)
            # pdf_url = await get_default_cover_letter(applicant_id)
            data = {
                "success": "Cover Letter Creation Initiated",
                # "improved_content": pdf_url,
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
            pdf_url = improve_cover_letter.delay(applicant_id)
            # pdf_url = await improve_cover_letter(applicant_id)
            data = {
                "success": "Cover Letter Improvement Initiated",
                # "improved_content": pdf_url,
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
            return_data = optimize_cover_letter.delay(applicant_id, job_post_id)
            # return_data = await optimize_cover_letter(applicant_id, job_post_id)
            data = {
                "success": "Cover Letter Optimization Initiated",
                # "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class CoverLetterImprovementCustomizationView(View):
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
            return_data = customize_improved_cover_letter.delay(
                applicant_id, custom_instruction
            )
            # return_data = await customize_improved_cover_letter(
            #     applicant_id, custom_instruction
            # )
            data = {
                "success": "Cover Letter Improvement Customization Initiated",
                # "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class CoverLetterOptimizationCustomizationView(View):
    """
    This view handles cover letter optimization. It does not interact with the database directly,
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
            return_data = customize_optimized_cover_letter.delay(
                applicant_id, job_post_id, custom_instruction
            )
            # return_data = await customize_optimized_cover_letter(
            #     applicant_id, job_post_id, custom_instruction
            # )
            data = {
                "success": "Cover Letter Optimization Customization Initiated",
                # "optimized_content": return_data,
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# ============================> COVER LETTER <============================


# ============================> JOB POST <============================
class JobOptimizationView(View):
    """
    This view handles job post optimization. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """

    serializer_class = None

    async def get(self, request, job_id, format=None):
        # feedback_only = request.query_params.get("feedback", "false").lower() == "true"
        try:
            optimized_job_post_content = optimize_job_post.delay(job_id)
            # optimized_job_post_content = await optimize_job_post(job_id)
            # might need to use the mark down dangerous html before pushing to frontend
            return JsonResponse(
                {
                    "success": "Job Optimization Initiated",
                    # "optimized_content": optimized_job_post_content,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================> JOB POST <============================


# http://127.0.0.1:8000/api/optimizers/optimize-job-post/654194177b7c7c8236e8541f/
# http://127.0.0.1:8000/api/optimizers/optimize-job-post/654194177b7c7c8236e8541f/?feedback=true
# http://127.0.0.1:8000/api/optimizers/optimize-resume/63a6af57677ed8a015025a62/654194177b7c7c8236e8541f/
# applicant_id 63a6af57677ed8a015025a62
# job_post_id 654194177b7c7c8236e8541f
# job_post_id = 65aa68567bd03fff776fbfcf
