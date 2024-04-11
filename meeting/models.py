from django.db import models


class InterviewTranscript(models.Model):
    transcript_id = models.CharField(max_length=100, unique=True)
    candidate_name = models.CharField(max_length=100, blank=True, null=True)
    interview_date = models.DateField(blank=True, null=True)
    transcript = models.TextField()

    def __str__(self):
        return f"Interview id {self.transcript_id} on {self.interview_date}"


class Analysis(models.Model):
    transcript = models.ForeignKey(InterviewTranscript, on_delete=models.CASCADE)
    analysis_type = models.CharField(max_length=100)  # e.g., 'Communication Skills'
    result = models.TextField()
    task_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default="PENDING")

    def __str__(self):
        return f"{self.analysis_type} Analysis for {self.transcript.candidate_name}"


class CandidateFeedback(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    category = models.CharField(
        max_length=100
    )  # e.g., 'Strengths', 'Areas for Improvement'
    feedback = models.TextField()

    def __str__(self):
        return f"Candidate Feedback for {self.analysis.transcript.candidate_name}"


class RecruiterFeedback(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    category = models.CharField(
        max_length=100
    )  # e.g., 'Technical Skills', 'Soft Skills'
    feedback = models.TextField()

    def __str__(self):
        return f"Recruiter Feedback for {self.analysis.transcript.candidate_name}"
