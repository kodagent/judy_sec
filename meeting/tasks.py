from celery import shared_task

from meeting.candidate_analyzer import main_analysis as analysis_for_candidate
from meeting.models import Analysis, CandidateFeedback, RecruiterFeedback
from meeting.recruiter_analyzer import main_analysis as analysis_for_recruiter


@shared_task
def run_candidate_analysis(transcript_text, analysis_id):
    analysis = Analysis.objects.get(id=analysis_id)
    analysis.status = "STARTED"
    analysis.save()

    result = analysis_for_candidate(transcript_text)

    # Save candidate feedback
    for category, feedback in result["candidate_feedback"].items():
        CandidateFeedback.objects.create(
            analysis=analysis, category=category, feedback=feedback
        )

    analysis.result = result["overall_analysis"]
    analysis.status = "SUCCESS"
    analysis.save()

    return result


@shared_task
def run_recruiter_analysis(transcript_text, analysis_id):
    analysis = Analysis.objects.get(id=analysis_id)
    analysis.status = "STARTED"
    analysis.save()

    result = analysis_for_recruiter(transcript_text)

    # Save recruiter feedback
    for category, feedback in result["recruiter_feedback"].items():
        RecruiterFeedback.objects.create(
            analysis=analysis, category=category, feedback=feedback
        )

    analysis.result = result["overall_analysis"]
    analysis.status = "SUCCESS"
    analysis.save()

    return result
