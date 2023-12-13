from rest_framework.response import Response
from rest_framework.views import APIView

from meeting.candidate_analyzer import main_analysis as analysis_for_candidate
from meeting.models import (Analysis, CandidateFeedback, InterviewTranscript,
                            RecruiterFeedback)
from meeting.recruiter_analyzer import main_analysis as analysis_for_recruiter
from meeting.serializers import (AnalysisSerializer,
                                 CandidateFeedbackSerializer,
                                 InterviewTranscriptSerializer,
                                 RecruiterFeedbackSerializer)


def get_existing_candidate_analysis(transcript_id):
    try:
        transcript = InterviewTranscript.objects.get(id=transcript_id)
        analysis = Analysis.objects.filter(transcript=transcript)
        feedback = CandidateFeedback.objects.filter(analysis__in=analysis)
        return transcript, analysis, feedback
    except InterviewTranscript.DoesNotExist:
        return None, None, None


def get_existing_recruiter_analysis(transcript_id):
    try:
        transcript = InterviewTranscript.objects.get(id=transcript_id)
        analysis = Analysis.objects.filter(transcript=transcript)
        feedback = RecruiterFeedback.objects.filter(analysis__in=analysis)
        return transcript, analysis, feedback
    except InterviewTranscript.DoesNotExist:
        return None, None, None


class TranscriptAnalysis(APIView):
    async def post(self, request, format=None):
        transcript_id = request.data.get('transcript_id')
        transcript_text = request.data.get('transcript')

        # Check for existing analysis
        existing_transcript, existing_candidate_analysis, existing_candidate_feedback = get_existing_analysis(transcript_id)
        _, existing_recruiter_analysis, existing_recruiter_feedback = get_existing_recruiter_analysis(transcript_id)

        if existing_transcript and existing_candidate_analysis and existing_candidate_feedback and existing_recruiter_analysis and existing_recruiter_feedback:
            # Return existing data
            return Response({
                'transcript': InterviewTranscriptSerializer(existing_transcript).data,
                'candidate_analysis': AnalysisSerializer(existing_candidate_analysis, many=True).data,
                'candidate_feedback': CandidateFeedbackSerializer(existing_candidate_feedback, many=True).data,
                'recruiter_analysis': AnalysisSerializer(existing_recruiter_analysis, many=True).data,
                'recruiter_feedback': RecruiterFeedbackSerializer(existing_recruiter_feedback, many=True).data
            })

        # If not existing, process new analysis for both candidate and recruiter
        candidate_analysis_results = await analysis_for_candidate(transcript_text)
        recruiter_analysis_results = await analysis_for_recruiter(transcript_text)

        # Combine and return the results
        return Response({
            'candidate_analysis': candidate_analysis_results,
            'recruiter_analysis': recruiter_analysis_results
        })
