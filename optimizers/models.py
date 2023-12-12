from django.db import models


# Model for storing job posts received from the Recruiting Platform
class JobPost(models.Model):
    job_post_id = models.CharField(max_length=255, unique=True)  # ID from the Recruiting Platform
    title = models.CharField(max_length=255)
    description = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Model for storing cover letters received from the Recruiting Platform
class CoverLetter(models.Model):
    cover_letter_id = models.CharField(max_length=255, unique=True)  # ID from the Recruiting Platform
    content = models.TextField()
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE)  # Associated job post
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cover Letter for {self.job_post.title}"

# Common model for storing analysis data for both job posts and cover letters
class Analysis(models.Model):
    cover_letter = models.ForeignKey(CoverLetter, on_delete=models.CASCADE, null=True, blank=True)
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, null=True, blank=True)
    keyword_matches = models.JSONField()
    readability_score = models.FloatField(null=True, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    tone_analysis = models.JSONField(null=True, blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.cover_letter or self.job_post}"

# Common model for storing optimized content for both job posts and cover letters
class OptimizedContent(models.Model):
    original_cover_letter = models.ForeignKey(CoverLetter, on_delete=models.CASCADE, null=True, blank=True, related_name='original_cover_letter')
    original_job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, null=True, blank=True, related_name='original_job_post')
    optimized_content = models.TextField()
    analysis = models.ForeignKey(Analysis, on_delete=models.SET_NULL, null=True, blank=True)
    optimized_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Optimized Content for {self.original_cover_letter or self.original_job_post}"

# Model for storing resumes received from the Recruiting Platform
class Resume(models.Model):
    resume_id = models.CharField(max_length=255, unique=True)  # ID from the Recruiting Platform
    content = models.TextField()
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE)  # Associated job post
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume for {self.job_post.title}"

# Model for storing resume analysis data
class ResumeAnalysis(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    keyword_matches = models.JSONField()
    complexity_score = models.FloatField(null=True, blank=True)
    readability_score = models.FloatField(null=True, blank=True)
    section_feedback = models.JSONField()
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for Resume {self.resume.id}"

# Model for storing optimized resume content
class OptimizedResume(models.Model):
    original_resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    optimized_content = models.TextField()
    analysis = models.ForeignKey(ResumeAnalysis, on_delete=models.SET_NULL, null=True, blank=True)
    optimized_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Optimized Resume for {self.original_resume.job_post.title}"