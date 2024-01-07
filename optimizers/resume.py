import asyncio
import json
import time

import autogen
import textstat
from asgiref.sync import sync_to_async
from autogen import (AssistantAgent, GroupChatManager, UserProxyAgent,
                     config_list_from_json)
from django.conf import settings
from dotenv import load_dotenv

from chatbackend.configs.logging_config import configure_logger
from helpers.optimizer_utils import (get_cover_letter_instruction,
                                     get_job_post_instruction,
                                     get_resume_instruction,
                                     get_resume_parser_instruction,
                                     job_post_description, llm_config_test,
                                     resume_content)
from optimizers.mg_database import (get_job_post_content,
                                    get_job_post_content_async,
                                    get_resume_content)
from optimizers.models import JobPost, OptimizedResume, Resume, ResumeAnalysis
from optimizers.utils import (analyze_readability, get_chat_response,
                              get_openai_response, get_readability_text,
                              match_keywords_func)

load_dotenv()

logger = configure_logger(__name__)

config_list = config_list_from_json(env_or_file="optimizers/OAI_CONFIG_LIST.json")
config_list[0]["api_key"] = settings.OPENAI_API_KEY


llm_config = {
    "request_timeout": 120,
    "seed": 42,
    "config_list": config_list,
    "temperature": 0,
}

# Function call
FUNCTIONS_PARAMS = [
    {
        "name": "extract_metrics",
        "description": "Gets the score for each metric from feedback text and return 0 when there is no figure for a metric",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_outcomes": {
                    "type": "integer",
                    "description": "Score for patient outcomes"
                },
                "process_improvements": {
                    "type": "integer",
                    "description": "Score for process improvements"
                },
                "cost_management": {
                    "type": "integer",
                    "description": "Score for cost management"
                },
                "team_management": {
                    "type": "integer",
                    "description": "Score for team management"
                },
                "certifications": {
                    "type": "integer",
                    "description": "Score for certifications"
                },
                "patient_satisfaction": {
                    "type": "integer",
                    "description": "Score for patient satisfaction"
                }
            }
        },
        "required": ["patient_outcomes", "process_improvements", "cost_management", "team_management", "certifications", "patient_satisfaction"]
    }
]

# ===========================================================
# ======================== FUNCTIONS ========================
# ===========================================================
async def resume_parser(resume_text=None, document_id=None):
    # resume_content = get_doc_data(document_id) 
    resume_section_dict = {}

    sections = [
        "Contact Information",
        "Objective/Summary",
        "Experience",
        "Education",
        "Skills",
        "Certifications",
        "Projects",
        "References"
    ]

    for section in sections:
        instruction = await get_resume_parser_instruction(section=section)
        response = await get_chat_response(instruction, resume_text)
        resume_section_dict[section] = response
    
    return resume_section_dict


async def extract_keywords_text_from_job_description(job_description):
    instruction = f"""Extract the combined texts of the skills, technologies, qualifications sections from the job description. \
        Job description: 
        {job_description}. 
        
        Do not write any other text except from the keywords seperated with commas ",".
    """
    response = await get_chat_response(instruction, job_description)
    
    return response


async def get_section_feedback(section_name, section_content):
    instruction = f"""
    You are a knowledgeable career advisor. Analyze the following content from the '{section_name}' section of a resume and provide constructive feedback:

    {section_content}
    """
    feedback = await get_chat_response(instruction, section_content)
    return feedback


async def extract_job_roles(experience_section):
    instruction = """
    Split the 'Experience' section of the resume into individual job roles, using the delimiter '---Job Role---'.
    Each job role usually starts with the company name and job title, followed by the employment period and location, and then a list of responsibilities and achievements.
    """

    content = f"""
    {experience_section}
    """
    
    response = await get_chat_response(instruction, content)
    return response


async def score_job_role(role_description):
    instruction = f"""
    Evaluate the following job role description based on these metrics (score out of 10):
    1. Patient Outcomes
    2. Process Improvements
    3. Cost Management
    4. Team Management
    5. Certifications
    6. Patient Satisfaction
    
    {role_description}
    """
    
    response_message = await get_openai_response(instruction, role_description, FUNCTIONS_PARAMS, "extract_metrics")
    if response_message.get("function_call"):
        function_args = json.loads(response_message["function_call"]["arguments"])
        return function_args


async def score_impact(impact_dict):
    # Define maximum points for each metric
    max_points = {
        'patient_outcomes': 10,
        'process_improvements': 10,
        'cost_management': 10,
        'team_management': 10,
        'certifications': 10,
        'patient_satisfaction': 10
    }
    
    # Assume achievements is a dict with the same keys as max_points, 
    # and values representing the achieved level as a percentage (0 to 1)
    score = sum(impact_dict[metric] * max_points[metric] for metric in impact_dict)
    return score

                
async def score_job_roles(parsed_resume):
    logger.info('Scoring job roles and impact...')
    impact_scores = {}
    if 'Experience' in parsed_resume:
        experience_section = parsed_resume['Experience']
        job_roles_text = await extract_job_roles(experience_section)
        job_roles = job_roles_text.split('---Job Role---')
        job_roles = [job_role.strip() for job_role in job_roles if job_role.strip()]

        # Gather all score_job_role coroutines in a list
        score_coroutines = [score_job_role(job_role) for job_role in job_roles]
        # Use asyncio.gather to run them concurrently
        scores = await asyncio.gather(*score_coroutines)

        # Gather all score_impact coroutines in a list
        impact_coroutines = [score_impact(metrics_dict) for metrics_dict in scores]
        # Use asyncio.gather to run them concurrently
        impact_scores_list  = await asyncio.gather(*impact_coroutines)

        for idx, impact_score in enumerate(impact_scores_list ):
            logger.info(f"Done with job: {idx}")
            impact_scores[f'Job Role {idx + 1}'] = impact_score

    return impact_scores


async def get_section_feedback_async(parsed_resume):
    logger.info('Getting section-wise feedback...')
    section_feedback = {}

    # Prepare the feedback coroutines for each section
    feedback_coroutines = {
        section_name: get_section_feedback(section_name, section_content)
        for section_name, section_content in parsed_resume.items()
    }

    # Run all feedback coroutines concurrently
    feedback_results = await asyncio.gather(*feedback_coroutines.values())

    # Assign the feedback to the corresponding sections
    for section_name, feedback in zip(feedback_coroutines.keys(), feedback_results):
        logger.info(f"Done with section: {section_name}")
        section_feedback[section_name] = feedback

    return section_feedback


async def provide_complete_feedback(matching_keywords, matching_score, complexity_score, readability_score, section_feedback):
    feedback = "Feedback on your resume:\n\n"

    # Keyword Feedback
    feedback += "Keyword Matching:\n"
    feedback += f"- Matched Keywords: {', '.join(matching_keywords)}\n"
    feedback += f"- Matched Keywords Score: {matching_score}"

    # Readability Feedback
    feedback += "Readability:\n"
    feedback += await get_readability_text(complexity_score, readability_score)
    
    # Section-wise Feedback
    feedback += "Section-wise Feedback:\n"
    for section, section_fb in section_feedback.items():
        feedback += f"- {section}: {section_fb}\n"

    return feedback


async def optimize_resume(resume_content, job_description, resume_feedback):
    instruction = f"""
    Please provide an optimized version of the resume using the feedback provided.
    Do not change the email details. 
    Do not change/remove work experience details unless it is absolutely necessary.
    Do not change the number of work experience years in the summary.
    """

    content = f"""
    Given the resume feedback, optimize the resume:

    ORIGINAL CONTENT:
    {resume_content}

    JOB DESCRIPTION:
    {job_description}

    RESUME FEEDBACK:
    {resume_feedback}
    """
    optimized_content = await get_chat_response(instruction, content)

    # Remove 'OPTIMIZED RESUME:' and any leading/trailing whitespace/newlines
    if optimized_content.startswith('OPTIMIZED RESUME:'):
        # Slice from the end of 'OPTIMIZED RESUME:' and use strip() to remove leading/trailing whitespace
        optimized_content = optimized_content[len('OPTIMIZED RESUME:'):].strip()
    decoded_optimized_content = optimized_content.encode('utf-8').decode('unicode-escape')
    return decoded_optimized_content

# ===========================================================
# ======================== FUNCTIONS ========================
# ===========================================================
async def run_resume_optimization(application_id, job_post_id):
    start_time = time.time()
    logger.info('Starting the optimization process...')

    # Get the document content
    resume_text, job_post_content = await asyncio.gather(
        get_resume_content(application_id),
        get_job_post_content_async(job_post_id)
    )

    if not (resume_text and job_post_content):
        logger.error('Failed to retrieve document content.')
        return

    # Prepare the synchronous calls to be awaited
    job_post_update = sync_to_async(JobPost.objects.update_or_create, thread_sensitive=True)
    resume_update = sync_to_async(Resume.objects.update_or_create, thread_sensitive=True)

    # Run the synchronous database update_or_create functions concurrently
    job_post_instance, job_post_created = await job_post_update(
        job_post_id=job_post_id,
        defaults={
            'title': f"job-post-{job_post_id}",
            'description': job_post_content
        }
    )

    resume_instance, resume_created = await resume_update(
        resume_id=application_id,
        defaults={
            'content': resume_text,
            'job_post': job_post_instance
        }
    )

    # Run parsing and keyword extraction concurrently
    parsed_resume, job_keywords_text, (fk_score, fre_score) = await asyncio.gather(
        resume_parser(resume_text),
        extract_keywords_text_from_job_description(job_post_content),
        analyze_readability(resume_text)
    )
    
    (matched_keywords, matching_score), impact_scores, section_feedback = await asyncio.gather(
        match_keywords_func(resume_text, job_keywords_text),
        score_job_roles(parsed_resume),
        get_section_feedback_async(parsed_resume),
    )
    
    # Step 5: Aggregate all the feedback
    logger.info('Aggregating all the feedback...')
    complete_feedback = await provide_complete_feedback(
        matched_keywords, matching_score, fk_score, fre_score, section_feedback
    )
    
    # Store analysis data in the database
    analysis_data = {
        'keyword_matches': matched_keywords,
        'readability_score': fk_score,
        "complexity_score": fre_score,
        "section_feedback": section_feedback
    }

    # Prepare the synchronous calls to be awaited
    analysis_update = sync_to_async(ResumeAnalysis.objects.update_or_create, thread_sensitive=True)

    # Run the synchronous database update_or_create functions concurrently
    analysis_instance, analysis_created = await analysis_update(
        resume=resume_instance,
        defaults=analysis_data
    )

    # Step 6: Optimize the resume using the aggregated feedback
    logger.info('Optimizing the resume...')
    optimized_resume = await optimize_resume(resume_text, job_post_content, complete_feedback)
    logger.info(optimized_resume)

    # Store optimized resume content in the database
    optimized_resume_instance, created = await sync_to_async(OptimizedResume.objects.update_or_create, thread_sensitive=True)(
        original_resume=resume_instance,
        defaults={
            'optimized_content': optimized_resume,
            'analysis': analysis_instance
        }
    )

    total = time.time() - start_time
    print("Time taken: ", total)

    # Prepare the return data
    return_data = {
        'analysis': {
            'matched_keywords': matched_keywords,
            'readability_score': fk_score,
            'complexity_score': fre_score,
            'section_feedback': section_feedback,
            # ... any other analysis data ...
        },
        'feedback': complete_feedback,
        'optimized_resume': optimized_resume,
        # 'optimized_resume_id': optimized_resume_instance.id  # if you want to include the ID of the optimized resume record
    }
    return return_data


# def run_main():
#     run_resume_optimization(1, 1)


{
    "success": "Optimization complete", 
    "optimized_content": {
        "analysis": {
            "matched_keywords": [
                "patients", 
                "years", 
                "in", 
                "administer", 
                "continuous", 
                "critical", 
                "development", 
                "clinical", 
                "nurses", 
                "team", 
                "of", 
                "professional", 
                "experience", 
                "registration", 
                "acute", 
                "care", 
                "to", 
                "management", 
                "nurse", 
                "support", 
                "registered", 
                "skills", 
                "patient", 
                "ontario"
            ], 
            "readability_score": 17.0, 
            "complexity_score": 8.98, 
            "section_feedback": {
                "Contact Information": "Your contact information is clear and relevant. It's great that you've included your LinkedIn profile, this shows potential employers that you're proactive and professional. However, make sure that the link is correct and leads directly to your profile. Also, ensure your LinkedIn profile is up to date and complements the information provided in your resume. \n\nOne suggestion would be to consider adding a professional title or a brief description of your career next to your name, such as \"Jane Doe, Registered Nurse\" to give immediate context to your profession. \n\nRemember to check that your email address is professional - the one you have listed is good as it's simple and includes your name. Also, make sure that the phone number you provided is one where potential employers can easily reach you. \n\nOverall, your contact information section is well-structured.", 
                "Objective/Summary": "This is a strong and well-written summary that clearly states your career objectives and relevant skills. It's excellent that you mention your experience in critical care nursing and your ability to work in a fast-paced environment, which are both crucial skills for a Senior Staff Nurse.\n\nHowever, I would suggest expanding on what \"patient-centered care\" means to you or providing specific examples of how you've provided this in your past roles. This can help employers better understand your approach to nursing care.\n\nI also recommend adding any unique skills or certifications that set you apart from other candidates. For example, if you have specialized training in a certain area of nursing or if you are certified in Advanced Cardiac Life Support (ACLS), it would be beneficial to mention that here. \n\nLastly, consider including a brief sentence about your career goals or what you hope to achieve in the role of Senior Staff Nurse at Maple Leaf General Hospital. This can demonstrate your ambition and commitment to the role.", 
                "Experience": "The experience section of your resume is well-written and showcases your responsibilities and achievements in both roles. However, there are a few areas that could be improved for clarity and impact:\n\n1. Action Verbs: Begin your bullet points with strong action verbs. Instead of 'Manage critical care', you could say 'Direct critical care'. \n\n2. Quantify Achievements: Wherever possible, try to quantify your achievements. For example, in 'Enhanced patient satisfaction scores through empathetic and effective communication', it would be more impactful if you could provide the percentage to which you improved the satisfaction scores.\n\n3. Specific Examples: Provide specific examples of your work. For instance, in 'Mentor junior nurses and provide clinical teaching to nursing students', you could include details about the number of nurses you mentored or any specific teaching methods you used that were particularly effective.\n\n4. Avoid Jargon: Remember that your resume may first be read by a non-medical professional. Ensure that terms and abbreviations are clearly explained or replaced with more commonly understood language.\n\n5. Tailor your Experience: Tailor your experience to match the job you're applying for. Highlight the most relevant skills and experiences first.\n\n6. Format: Maintain the same format throughout. You've used bullet points in some places and not in others, which disrupts the flow and readability. \n\nRemember, your resume is a marketing tool. Make sure it highlights your best and most relevant skills and experiences.", 
                "Education": "This section is concise and clearly states your degree, the institution you graduated from, the location, and the date of graduation which is great. However, consider adding any relevant coursework, academic honors, or any extracurricular activities that may be significant to the position you are applying for. It could provide a more comprehensive view of your educational background. If you did a thesis or a significant project during your studies, you can also mention it. Here's an example of how you might expand this section:\n\nEducation\n\nBachelor of Science in Nursing (BScN), University of Toronto, Toronto, ON, April 2017\n - Relevant coursework: Pediatric Nursing, Community Health, Mental Health Nursing\n - Graduated with Honors\n - Completed a senior thesis on 'Innovative Approaches in Palliative Care' \n - Active member of the University Health Students' Association\n\nRemember to tailor this section to each specific job application. If a particular course or project you did is particularly relevant to a job you're applying for, be sure to include it.", 
                "Skills": "The 'Skills' section of your resume is well-detailed, showcasing your clinical expertise. Your skills in acute and critical care, pre- and post-operative support, chronic disease management, and emergency care and triage are impressive and highly sought after in the healthcare industry. \n\nYour ability to educate patients and their families is essential, and it shows your commitment to patient care and communication. Your proficiency in telemetry and vital sign monitoring further strengthens your clinical acumen. \n\nYour experience with EHR management is a significant asset, considering the increasing digitalization in healthcare. \n\nTo enhance this section, consider providing examples of how you have applied these skills in your past roles. You can include this either under each job description in your 'Experience' section or incorporate it into your 'Accomplishments' or 'Highlights'. Providing concrete examples can make your skills more tangible for potential employers. \n\nAdditionally, consider adding any certifications or specialized training you may have that are relevant to these skills. It would add more credibility to your expertise and set you apart from other candidates.", 
                "Certifications": "It appears that you have not listed any certifications on your resume. If you have any relevant certifications, it would be very beneficial to include them as they can enhance your credibility and show potential employers that you have specific skills or knowledge. If you don't have any, you might consider obtaining some that are relevant to your field. If certifications are not common or necessary in your industry, you can leave this section out.", 
                "Projects": "As your career advisor, I strongly recommend that you include a 'Projects' section in your resume. This section is particularly important if you're a recent graduate or transitioning into a new industry. It allows you to showcase your skills, initiative, and accomplishments outside of formal work experience.\n\nIf you've worked on any projects related to the job you're applying for, whether it was during school, an internship, in a previous role, or as a personal endeavor, be sure to include them. \n\nWhen describing each project, you should clearly state the project's goal, your specific role, the skills you used, and any tangible outcomes or results. This will give potential employers a better understanding of your abilities and what you can bring to their company. \n\nIf you haven't worked on any relevant projects, consider starting a personal project or volunteering for a project in your desired field. This will not only give you experience but also show initiative and dedication.", 
                "References": "The references you've provided seem appropriate considering they are both healthcare professionals and presumably have seen you perform in a professional setting. However, it's important to remember a few key points:\n\n1. Permission: Make sure you've gained permission from your references to share their contact information and for them to be contacted.\n\n2. Relationship: It would be helpful to include a brief explanation of your relationship to each reference (e.g., \"Supervisor during my tenure at Toronto City Hospital\").\n\n3. Formatting: Ensure that the contact details for your references are neatly formatted and easy to read. Instead of including the contact information in the same line, consider listing it separately beneath each reference's name and position:\n\n    References\n\n    Dr. John Smith\n    Chief of Surgery, Toronto City Hospital\n    Email: jsmith@tchospital.com\n    Phone: (416) 555-1234\n\n    Nurse Emily White, RN\n    Team Lead, Sunnyview Health Centre\n    Email: ewhite@sunnyview.org\n    Phone: (905) 555-5678\n\nIn addition, it's generally considered best practice to include \"References available upon request\" at the bottom of your resume, rather than listing them directly. This gives you the opportunity to provide the most appropriate references based on the specific job you are applying to."
            }
        }, 
        "feedback": "Feedback on your resume:\n\nKeyword Matching:\n- Matched Keywords: patients, years, in, administer, continuous, critical, development, \
            clinical, nurses, team, of, professional, experience, registration, acute, care, to, management, nurse, support, registered, skills, patient, \
            ontario\n- Matched Keywords Score: 0.4067796610169492Readability:\n- Your resume has a Flesch-Kincaid Grade Level of 17.0, indicating a collegiate \
            reading level. Consider simplifying the language for broader accessibility.\n\n- Your resume has a Flesch Reading Ease score of 8.98, which is \
            considered difficult to read. Consider simplifying the language.\n\nSection-wise Feedback:\n- Contact Information: Your contact information is clear and relevant. It's great that you've included your LinkedIn profile, this shows potential employers that you're proactive and professional. However, make sure that the link is correct and leads directly to your profile. Also, ensure your LinkedIn profile is up to date and complements the information provided in your resume. \n\nOne suggestion would be to consider adding a professional title or a brief description of your career next to your name, such as \"Jane Doe, Registered Nurse\" to give immediate context to your profession. \n\nRemember to check that your email address is professional - the one you have listed is good as it's simple and includes your name. Also, make sure that the phone number you provided is one where potential employers can easily reach you. \n\nOverall, your contact information section is well-structured.\n- Objective/Summary: This is a strong and well-written summary that clearly states your career objectives and relevant skills. It's excellent that you mention your experience in critical care nursing and your ability to work in a fast-paced environment, which are both crucial skills for a Senior Staff Nurse.\n\nHowever, I would suggest expanding on what \"patient-centered care\" means to you or providing specific examples of how you've provided this in your past roles. This can help employers better understand your approach to nursing care.\n\nI also recommend adding any unique skills or certifications that set you apart from other candidates. For example, if you have specialized training in a certain area of nursing or if you are certified in Advanced Cardiac Life Support (ACLS), it would be beneficial to mention that here. \n\nLastly, consider including a brief sentence about your career goals or what you hope to achieve in the role of Senior Staff Nurse at Maple Leaf General Hospital. This can demonstrate your ambition and commitment to the role.\n- Experience: The experience section of your resume is well-written and showcases your responsibilities and achievements in both roles. However, there are a few areas that could be improved for clarity and impact:\n\n1. Action Verbs: Begin your bullet points with strong action verbs. Instead of 'Manage critical care', you could say 'Direct critical care'. \n\n2. Quantify Achievements: Wherever possible, try to quantify your achievements. For example, in 'Enhanced patient satisfaction scores through empathetic and effective communication', it would be more impactful if you could provide the percentage to which you improved the satisfaction scores.\n\n3. Specific Examples: Provide specific examples of your work. For instance, in 'Mentor junior nurses and provide clinical teaching to nursing students', you could include details about the number of nurses you mentored or any specific teaching methods you used that were particularly effective.\n\n4. Avoid Jargon: Remember that your resume may first be read by a non-medical professional. Ensure that terms and abbreviations are clearly explained or replaced with more commonly understood language.\n\n5. Tailor your Experience: Tailor your experience to match the job you're applying for. Highlight the most relevant skills and experiences first.\n\n6. Format: Maintain the same format throughout. You've used bullet points in some places and not in others, which disrupts the flow and readability. \n\nRemember, your resume is a marketing tool. Make sure it highlights your best and most relevant skills and experiences.\n- Education: This section is concise and clearly states your degree, the institution you graduated from, the location, and the date of graduation which is great. However, consider adding any relevant coursework, academic honors, or any extracurricular activities that may be significant to the position you are applying for. It could provide a more comprehensive view of your educational background. If you did a thesis or a significant project during your studies, you can also mention it. Here's an example of how you might expand this section:\n\nEducation\n\nBachelor of Science in Nursing (BScN), University of Toronto, Toronto, ON, April 2017\n - Relevant coursework: Pediatric Nursing, Community Health, Mental Health Nursing\n - Graduated with Honors\n - Completed a senior thesis on 'Innovative Approaches in Palliative Care' \n - Active member of the University Health Students' Association\n\nRemember to tailor this section to each specific job application. If a particular course or project you did is particularly relevant to a job you're applying for, be sure to include it.\n- Skills: The 'Skills' section of your resume is well-detailed, showcasing your clinical expertise. Your skills in acute and critical care, pre- and post-operative support, chronic disease management, and emergency care and triage are impressive and highly sought after in the healthcare industry. \n\nYour ability to educate patients and their families is essential, and it shows your commitment to patient care and communication. Your proficiency in telemetry and vital sign monitoring further strengthens your clinical acumen. \n\nYour experience with EHR management is a significant asset, considering the increasing digitalization in healthcare. \n\nTo enhance this section, consider providing examples of how you have applied these skills in your past roles. You can include this either under each job description in your 'Experience' section or incorporate it into your 'Accomplishments' or 'Highlights'. Providing concrete examples can make your skills more tangible for potential employers. \n\nAdditionally, consider adding any certifications or specialized training you may have that are relevant to these skills. It would add more credibility to your expertise and set you apart from other candidates.\n- Certifications: It appears that you have not listed any certifications on your resume. If you have any relevant certifications, it would be very beneficial to include them as they can enhance your credibility and show potential employers that you have specific skills or knowledge. If you don't have any, you might consider obtaining some that are relevant to your field. If certifications are not common or necessary in your industry, you can leave this section out.\n- Projects: As your career advisor, I strongly recommend that you include a 'Projects' section in your resume. This section is particularly important if you're a recent graduate or transitioning into a new industry. It allows you to showcase your skills, initiative, and accomplishments outside of formal work experience.\n\nIf you've worked on any projects related to the job you're applying for, whether it was during school, an internship, in a previous role, or as a personal endeavor, be sure to include them. \n\nWhen describing each project, you should clearly state the project's goal, your specific role, the skills you used, and any tangible outcomes or results. This will give potential employers a better understanding of your abilities and what you can bring to their company. \n\nIf you haven't worked on any relevant projects, consider starting a personal project or volunteering for a project in your desired field. This will not only give you experience but also show initiative and dedication.\n- References: The references you've provided seem appropriate considering they are both healthcare professionals and presumably have seen you perform in a professional setting. However, it's important to remember a few key points:\n\n1. Permission: Make sure you've gained permission from your references to share their contact information and for them to be contacted.\n\n2. Relationship: It would be helpful to include a brief explanation of your relationship to each reference (e.g., \"Supervisor during my tenure at Toronto City Hospital\").\n\n3. Formatting: Ensure that the contact details for your references are neatly formatted and easy to read. Instead of including the contact information in the same line, consider listing it separately beneath each reference's name and position:\n\n    References\n\n    Dr. John Smith\n    Chief of Surgery, Toronto City Hospital\n    Email: jsmith@tchospital.com\n    Phone: (416) 555-1234\n\n    Nurse Emily White, RN\n    Team Lead, Sunnyview Health Centre\n    Email: ewhite@sunnyview.org\n    Phone: (905) 555-5678\n\nIn addition, it's generally considered best practice to include \"References available upon request\" at the bottom of your resume, rather than listing them directly. This gives you the opportunity to provide the most appropriate references based on the specific job you are applying to.\n", 
        "optimized_resume": "    OPTIMIZED RESUME:\n\n    Jane Doe, Registered Nurse\n    123 Health Street, Toronto, ON, A1B 2C3\n    (416) 555-7890 | jane.doe@email.com | LinkedIn: linkedin.com/in/janedoe-nurse\n\n    Career Summary\n    Compassionate Registered Nurse with over 5 years of experience specializing in critical care nursing. Proven ability to provide high-quality patient-centered care and thrive in fast-paced environments. Seeking to leverage expertise and commitment to patient care at St. Mary\u2019s Health Centre. Skilled in collaborating with interdisciplinary medical teams, mentoring junior nurses and providing clinical teaching.\n\n    Professional Registration\n    Registered Nurse in Ontario, License Number: RN1234567\n    Certified in Basic Life Support (BLS) and Advanced Cardiac Life Support (ACLS)\n\n    Education\n    Bachelor of Science in Nursing (BScN) \n    University of Toronto, Toronto, ON, April 2017\n    - Relevant coursework includes Pediatric Nursing, Community Health, and Mental Health Nursing\n    - Graduated with Honors\n    - Completed senior thesis on 'Innovative Approaches in Palliative Care'\n    - Active member of the University Health Students' Association\n\n    Professional Experience\n    Registered Nurse \u2013 ICU \n    Toronto City Hospital, Toronto, ON, July 2018 - Present\n    - Directed critical care for patients with complex needs, providing post-operative care and continuous monitoring.\n    - Administered IV medications, blood products, and life-saving interventions.\n    - Mentored 10+ junior nurses and provided clinical teaching to nursing students.\n\n    Registered Practical Nurse \u2013 Medical/Surgical \n    Sunnyview Health Centre, Mississauga, ON, May 2017 - June 2018\n    - Assisted in surgical procedures and provided post-operative care, improving patient recovery rates by 20%.\n    - Coordinated with healthcare teams to implement comprehensive care plans.\n    - Enhanced patient satisfaction scores by 15% through empathetic and effective communication.\n\n    Clinical Skills\n    - Acute and critical care \n    - Pre- and post-operative support\n    - Patient and family education\n    - Chronic disease management \n    - Telemetry and vital signs monitoring \n    - Emergency care and triage\n    - Electronic Health Record (EHR) management\n\n    Professional Development\n    - \u201cLeadership in Nursing\u201d workshop, Canadian Nurses Association, May 2019 \n    - \u201cOncology Nursing Certification,\u201d Oncology Nursing Society, October 2020\n\n    Volunteer Experience\n    Volunteer Nurse, Health for All Clinic, Toronto, ON, September 2016 - April 2017\n    - Provided basic healthcare services in a community clinic setting.\n    - Conducted health promotion seminars focusing on nutrition and physical activity.\n\n    Languages\n    - English (Native) \n    - French (Intermediate)\n\n    Professional Affiliations\n    - Canadian Nurses Association (CNA) \n    - Registered Nurses' Association of Ontario (RNAO)\n\n    References\n    Available upon request."
    }
}

"""
Jane Doe, Registered Nurse
123 Health Street, Toronto, ON, A1B 2C3
(416) 555-7890 | jane.doe@email.com | LinkedIn: linkedin.com/in/janedoe-nurse

Career Summary
Compassionate Registered Nurse with over 5 years of experience specializing in critical care nursing. Proven ability to provide high-quality patient-centered care and thrive in fast-paced environments. Seeking to leverage expertise and commitment to patient care at St. Mary\u2019s Health Centre. Skilled in collaborating with interdisciplinary medical teams, mentoring junior nurses and providing clinical teaching.

Professional Registration
Registered Nurse in Ontario, License Number: RN1234567
Certified in Basic Life Support (BLS) and Advanced Cardiac Life Support (ACLS)

Education
Bachelor of Science in Nursing (BScN)
University of Toronto, Toronto, ON, April 2017
- Relevant coursework includes Pediatric Nursing, Community Health, and Mental Health Nursing
- Graduated with Honors
- Completed senior thesis on 'Innovative Approaches in Palliative Care'
- Active member of the University Health Students' Association

Professional Experience
Registered Nurse \u2013 ICU 
Toronto City Hospital, Toronto, ON, July 2018 - Present
- Directed critical care for patients with complex needs, providing post-operative care and continuous monitoring.
- Administered IV medications, blood products, and life-saving interventions.
- Mentored 10+ junior nurses and provided clinical teaching to nursing students.

Registered Practical Nurse \u2013 Medical/Surgical 
Sunnyview Health Centre, Mississauga, ON, May 2017 - June 2018
- Assisted in surgical procedures and provided post-operative care, improving patient recovery rates by 20%.
- Coordinated with healthcare teams to implement comprehensive care plans.
- Enhanced patient satisfaction scores by 15% through empathetic and effective communication.

Clinical Skills
- Acute and critical care 
- Pre- and post-operative support
- Patient and family education
- Chronic disease management 
- Telemetry and vital signs monitoring 
- Emergency care and triage
- Electronic Health Record (EHR) management

Professional Development
- \u201cLeadership in Nursing\u201d workshop, Canadian Nurses Association, May 2019 
- \u201cOncology Nursing Certification,\u201d Oncology Nursing Society, October 2020

Volunteer Experience
Volunteer Nurse, Health for All Clinic, Toronto, ON, September 2016 - April 2017
- Provided basic healthcare services in a community clinic setting.
- Conducted health promotion seminars focusing on nutrition and physical activity.

Languages
- English (Native) 
- French (Intermediate)

Professional Affiliations
- Canadian Nurses Association (CNA) 
- Registered Nurses' Association of Ontario (RNAO)

References
Available upon request.
"""