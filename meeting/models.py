from django.db import models


class InterviewTranscript(models.Model):
    transcript_id = models.CharField(max_length=100, unique=True)
    candidate_name = models.CharField(max_length=100)
    interview_date = models.DateField()
    transcript = models.TextField()

    def __str__(self):
        return f"Interview with {self.candidate_name} on {self.interview_date}"


class Analysis(models.Model):
    transcript = models.ForeignKey(InterviewTranscript, on_delete=models.CASCADE)
    analysis_type = models.CharField(max_length=100)  # e.g., 'Communication Skills'
    result = models.TextField()

    def __str__(self):
        return f"{self.analysis_type} Analysis for {self.transcript.candidate_name}"


class CandidateFeedback(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    feedback = models.TextField()

    def __str__(self):
        return f"Candidate Feedback for {self.analysis.transcript.candidate_name}"


class RecruiterFeedback(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    feedback = models.TextField()

    def __str__(self):
        return f"Recruiter Feedback for {self.analysis.transcript.candidate_name}"
