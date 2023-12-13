from django.conf import settings
from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI

from chatbackend.logging_config import configure_logger
from helpers.optimizer_utils import job_post_content, job_post_description
from optimizers.mg_database import get_job_post_content
from optimizers.models import Analysis, JobPost, OptimizedContent

# Logging setup
logger = configure_logger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_ROLE = "system"
USER_ROLE = "user"


def get_openai_response(INSTRUCTION, content, functions=None, function_name=None):
    messages = [
        {"role": SYSTEM_ROLE, "content": INSTRUCTION},
        {"role": USER_ROLE, "content": content}
    ]

    if functions:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            functions=functions,
            function_name=function_name,
        )
    else:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
        )

    return response.choices[0].message.content


def get_feedback(job_post_content):
    instruction = f"""
    As an experienced recruiter, review the following job post and provide detailed feedback analysis to help improve and optimize it.

    Use these considerations below in your review:
    - Enhancing SEO (Search Engine Optimization):
    - Keyword Optimization
    - Industry-Specific Terminology

    - Improving Clarity of Job Descriptions:
    - Clear Job Titles
    - Concise Job Duties
    - Required Qualifications
    """
    response = get_openai_response(instruction, job_post_content)
    return response


def optimize_job_post(job_post_content):
    instruction = f"""As an experienced recruiter, review the following job post and optimize and improve the job post. \
        ENSURE NOT TO WRITE ANY ADDITIONAL TEXT TO THE OPTIMIZED TEXT.

    Use these considerations below in your review:
    - Enhancing SEO (Search Engine Optimization):
    - Keyword Optimization
    - Industry-Specific Terminology

    - Improving Clarity of Job Descriptions:
    - Clear Job Titles
    - Concise Job Duties
    - Required Qualifications
    """

    content = f"""
    {job_post_content}
    """
    
    # JOB POST FEEDBACK:
    # {post_feedback}
    # """
    response = get_openai_response(instruction, content)
    return response


def run_job_post_optimization(job_post_id, feedback=False):
    # Get the document content
    job_post_content = get_job_post_content(job_post_id)

    if feedback:
        content_feedback = get_feedback(job_post_content)
        return content_feedback

    # Try to get the JobPost instance if it exists, or create a new one if it doesn't
    job_post_instance, created = JobPost.objects.get_or_create(
        job_post_id=job_post_id,
        defaults={
            'title': f"job-post-{job_post_id}",
            'description': job_post_content
        }
    )

    # If the JobPost already exists, update its content
    if not created:
        job_post_instance.description = job_post_content
        job_post_instance.save()
        logger.info(f"JobPost with ID {job_post_id} updated with new content.")

    # # this is causing an elongated time
    # post_feedback = get_feedback(job_post_content)
    # logger.info(f"----------------------- POST FEEDBACK -----------------------")
    # logger.info(f"{post_feedback}")

    # # Save analysis data to the database
    # analysis_data = {
    #     'job_post': job_post_instance,
    #     # ... other analysis data ...
    # }
    # analysis_instance = Analysis.objects.create(**analysis_data)

    optimized_content = optimize_job_post(job_post_content)
    logger.info(f"----------------------- OPTIMIZED CONTENT -----------------------")
    logger.info(f"{optimized_content}")

    # Save optimized content to the database
    optimized_content_instance = OptimizedContent.objects.create(
        original_job_post=job_post_instance,
        optimized_content=optimized_content,
        # analysis=analysis_instance
    )

    return optimized_content


{
    "success": "Optimization complete",
    "optimized_content": "Job Title: Full-Time Registered Nurse (RN) - Acute Care\nLocation: Ontario\n\nAbout St. Mary’s Health Centre:\nA top-tier healthcare institution, St. Mary's Health Centre is recognized for its commitment to delivering innovative, high-quality patient care. Our acute care department prides itself on its dynamic team working tirelessly in a high-paced setting to cater to patients' diverse medical needs.\n\nJob Role:\nWe're actively seeking a passionate Registered Nurse (RN) to join our acute care team. The ideal candidate possesses a strong desire to provide exceptional care to patients and enhance our collaborative patient-focused environment.\n\nKey Responsibilities:\n• Conduct thorough patient assessments and formulate care plans in collaboration with the healthcare team\n• Safely administer medications, maintain precise patient records, and monitor for potential side effects\n• Provide hands-on patient care, including wound management and support for daily activities\n• Educate patients and their families on managing illnesses and preventive care\n• Use critical thinking and problem-solving skills to make informed clinical decisions and manage acute patient care effectively\n• Participate in ongoing improvement initiatives and professional development activities\n\nQualifications:\n• Current registration in good standing with the College of Nurses of Ontario (or eligible for registration)\n• BScN or equivalent recognized by the College of Nurses of Ontario\n• Minimum of 2 years' experience in an acute care setting preferred\n• Mandatory CPR certification;  ACLS certification is a plus\n• Proven ability to work independently and as part of a multi-disciplinary team \n• Excellent communication and interpersonal skills\n• Legal entitlement to work in Canada\n\nWhat We Offer:\n• Competitive salary with a comprehensive benefits package\n• Opportunities for professional growth, including access to continuing education\n• A supportive work environment aimed at promoting work-life balance\n• Access to on-site fitness facilities and wellness programs\n\nHow to Apply:\nInterested applicants are invited to submit their resume, a cover letter, and the contact information for two professional references. Apply via our online portal at St. Mary's Health Centre Careers or email your application to recruitment@stmaryshealth.ca.\n\nApplication Closing Date: [e.g., December 1, 2023]\n\nSt. Mary’s Health Centre is an equal opportunity employer committed to diversity and inclusion. We welcome all qualified applicants for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability, veterans' status, Indigenous status, or any other legally protected factors. We provide accommodations for applicants with disabilities upon request during the recruitment process."
}

{
    "success": "Feedback retrieval complete",
    "post_feedback": "The job post is generally good and provides a clear understanding of the role and the organization. However, several improvements could be made to boost SEO and clarity:\n\nSEO Enhancement:\n- Keyword Optimization: Include more industry-specific keywords. For example, use terms like \"patient care,\" \"medical,\" \"healthcare,\" \"nursing,\" and \"acute care\" more frequently throughout the description.\n- Industry-specific Terminology: You've done well here, but incorporating terms like \"patient advocacy,\" \"acute care nursing,\" or \"clinical decision making,\" could enhance the job post's visibility.\n\nImproving Clarity of Job Descriptions:\n- Clear Job Titles: This area is well-covered. The job title \"Registered Nurse (RN)\" is clear and concise.\n- Concise Job Duties: You've detailed many roles such as administering medications, wound management, and patient education. However, some of the job responsibilities could be more directly linked to the term 'Registered Nurse'. For instance, instead of saying \"Utilize critical thinking and problem-solving skills to make clinical decisions and manage acute patient care effectively,\" try rephrasing it into something more RN relevant, like \"Provide effective acute patient care, using clinical decision-making skills backed by critical thinking and problem-solving abilities.\" \n- Required Qualifications: The qualifications are stated clearly. However, you could improve the readability by using bullet points instead of writing it out in paragraph form.\n\nLastly, you could consider adding a section that addresses \"What Makes You Stand Out\" or \"Preferred Qualifications,\" where you can include skills or qualifications that aren't necessary but would present an advantage (e.g., prior experience with certain software).\n\nRemember to reiterate your location and contact information at the end of the job to facilitate interested applicants. Keeping these pointers in mind should help optimize your job post."
}

"""
Job Title: Full-Time Registered Nurse (RN) - Acute Care
Location: Ontario

About St. Mary’s Health Centre:
A top-tier healthcare institution, St. Mary's Health Centre is recognized for its commitment to delivering innovative, high-quality patient care. Our acute care department prides itself on its dynamic team working tirelessly in a high-paced setting to cater to patients' diverse medical needs.

Job Role:
We're actively seeking a passionate Registered Nurse (RN) to join our acute care team. The ideal candidate possesses a strong desire to provide exceptional care to patients and enhance our collaborative patient-focused environment.

Key Responsibilities:
• Conduct thorough patient assessments and formulate care plans in collaboration with the healthcare team
• Safely administer medications, maintain precise patient records, and monitor for potential side effects
• Provide hands-on patient care, including wound management and support for daily activities
• Educate patients and their families on managing illnesses and preventive care
• Use critical thinking and problem-solving skills to make informed clinical decisions and manage acute patient care effectively
• Participate in ongoing improvement initiatives and professional development activities

Qualifications:
• Current registration in good standing with the College of Nurses of Ontario (or eligible for registration)
• BScN or equivalent recognized by the College of Nurses of Ontario
• Minimum of 2 years' experience in an acute care setting preferred
• Mandatory CPR certification;  ACLS certification is a plus
• Proven ability to work independently and as part of a multi-disciplinary team 
• Excellent communication and interpersonal skills
• Legal entitlement to work in Canada

What We Offer:
• Competitive salary with a comprehensive benefits package
• Opportunities for professional growth, including access to continuing education
• A supportive work environment aimed at promoting work-life balance
• Access to on-site fitness facilities and wellness programs

How to Apply:
Interested applicants are invited to submit their resume, a cover letter, and the contact information for two professional references. Apply via our online portal at St. Mary's Health Centre Careers or email your application to recruitment@stmaryshealth.ca.

Application Closing Date: [e.g., December 1, 2023]

St. Mary’s Health Centre is an equal opportunity employer committed to diversity and inclusion. We welcome all qualified applicants for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability, veterans' status, Indigenous status, or any other legally protected factors. We provide accommodations for applicants with disabilities upon request during the recruitment process."""


"""
The job post is generally good and provides a clear understanding of the role and the organization. However, several improvements could be made to boost SEO and clarity:

SEO Enhancement:
- Keyword Optimization: Include more industry-specific keywords. For example, use terms like "patient care," "medical," "healthcare," "nursing," and "acute care" more frequently throughout the description.
- Industry-specific Terminology: You've done well here, but incorporating terms like "patient advocacy," "acute care nursing," or "clinical decision making," could enhance the job post's visibility.

Improving Clarity of Job Descriptions:
- Clear Job Titles: This area is well-covered. The job title "Registered Nurse (RN)" is clear and concise.
- Concise Job Duties: You've detailed many roles such as administering medications, wound management, and patient education. However, some of the job responsibilities could be more directly linked to the term 'Registered Nurse'. For instance, instead of saying "Utilize critical thinking and problem-solving skills to make clinical decisions and manage acute patient care effectively," try rephrasing it into something more RN relevant, like "Provide effective acute patient care, using clinical decision-making skills backed by critical thinking and problem-solving abilities." 
- Required Qualifications: The qualifications are stated clearly. However, you could improve the readability by using bullet points instead of writing it out in paragraph form.

Lastly, you could consider adding a section that addresses "What Makes You Stand Out" or "Preferred Qualifications," where you can include skills or qualifications that aren't necessary but would present an advantage (e.g., prior experience with certain software).

Remember to reiterate your location and contact information at the end of the job to facilitate interested applicants. Keeping these pointers in mind should help optimize your job post.
"""