from django.urls import path

from meeting import views

urlpatterns = [
    path('transcript-analysis/', views.TranscriptAnalysis.as_view(), name='transcript_analysis'),
]


transcript = """
Recruiter: Good morning, and thank you for coming in today. I'm Alex, the recruitment lead for our nursing team. Could you start by telling me a little about yourself and your nursing experience?

Candidate (Jordan): Good morning, Alex. Thank you for having me. I'm Jordan. I've been a registered nurse for five years, with a focus on pediatric care. I've worked in both hospital and clinic settings, which has given me a diverse range of experiences in patient care, emergency response, and health education.

Recruiter: That's great to hear, Jordan. What motivated you to apply for this position in our hospital?

Jordan: I've always been passionate about providing compassionate and efficient care to patients. I believe your hospital's emphasis on patient-centered care and continuous learning aligns perfectly with my professional values and goals. I'm particularly excited about your initiatives in pediatric care innovation.

Recruiter: I'm glad our values resonate with you. Can you tell me about a challenging situation you've encountered in your nursing career and how you handled it?

Jordan: Certainly. Once, I had a pediatric patient who was extremely anxious about their treatment. I took the time to communicate with them at their level, using age-appropriate explanations and a calm demeanor. I also involved their parents in the process, ensuring they were comfortable and informed. This approach not only eased the patient's anxiety but also facilitated a smoother treatment process.

Recruiter: That's a wonderful approach. How do you keep your nursing knowledge and skills up to date?

Jordan: I'm committed to lifelong learning. I regularly attend professional workshops and seminars, and I'm part of a nursing study group. I also read nursing journals to keep abreast of the latest developments in healthcare.

Recruiter: Great to hear. Can you describe how you work in a team setting?

Jordan: Teamwork is crucial in nursing. I believe in clear communication, mutual respect, and collaboration. In my previous role, I worked closely with doctors, other nurses, and support staff. I always make sure to listen actively and contribute positively to our team's goals.

Recruiter: That's important in our hospital environment. How do you handle stressful situations?

Jordan: I try to stay calm and focused under pressure, prioritizing tasks and seeking support when necessary. I also practice self-care outside of work to maintain my well-being, which I believe is key to handling stress effectively.

Recruiter: Excellent. Do you have any questions for me about the role or our hospital?

Jordan: Yes, I'd like to know more about the opportunities for professional development and advancement within your nursing team.

Recruiter: We have a robust professional development program, including mentorship, ongoing training, and opportunities for advancement into leadership roles. We're committed to supporting our nurses' career growth.

Recruiter: Thank you, Jordan, for sharing your experiences and insights. We'll be in touch soon regarding the next steps in the recruitment process.

Jordan: Thank you, Alex, for considering my application. I look forward to the possibility of joining your team.
"""


# # Data to be sent in the request
# data = {
#     'transcript_id': '123',
#     'transcript': 'Your interview transcript here',
# }