from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendation.utilities.processing import JobRecommender

# Instantiate the recommender with the jobs data
recommender = JobRecommender()

class JobRecommendationView(APIView):
    """
    This view handles job recommendations. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """
    serializer_class = None
    
    def get(self, request, candidate_id, format=None):
        try:
            top_n_jobs = recommender.get_job_recommendations_by_id(candidate_id, top_n=10)
            return Response(top_n_jobs)
        except KeyError:
            return Response({"error": "Candidate ID not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CandidateRecommendationView(APIView):
    """
    This view handles candidate recommendations. It does not interact with the database directly,
    hence does not use a serializer_class. Instead, it relies on custom utility functions.
    """
    serializer_class = None

    def get(self, request, job_id, format=None):
        try:
            top_candidates = recommender.get_top_candidates_for_job_by_id(job_id, top_n=10)
            return Response(top_candidates)
        except KeyError:
            return Response({"error": "Job ID not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)