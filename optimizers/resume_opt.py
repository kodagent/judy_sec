import textstat
from django.conf import settings
from django.db import connections
from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI

from chatbackend.logging_config import configure_logger
from helpers.optimizer_utils import (get_cover_letter_instruction,
                                     get_job_post_instruction,
                                     get_resume_instruction,
                                     get_resume_parser_instruction,
                                     job_post_description, resume_content)

logger = configure_logger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_ROLE = "system"
USER_ROLE = "user"

def get_document_file_by_id(document_id):
    # Change this to suit mongo db
    try:
        with connections['giddaa_db'].cursor() as cursor:
            # cursor.execute('SELECT "Document" FROM "public"."Documents" WHERE "Id" = %s', [document_id])
            # cursor.execute('SELECT * FROM "public"."Documents" WHERE "Id" = %s', [document_id])
            cursor.execute('SELECT "Id", "Name", "Description", "Extension", "Document", "ExtraProperties" FROM "public"."Documents" WHERE "Id" = %s', [document_id])

            row = cursor.fetchone()
            if row:
                # Assuming columns are id, name, description, extension, document, extraProperties
                document_data = {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "extension": row[3],
                    "document": row[4],
                    "extraProperties": row[5]
                }
                logger.info(f"This is the document data: {document_data}")
                return document_data
            else:
                return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None
    

def get_doc_data(document_id):
    document_data = get_document_file_by_id(document_id)
    public_url = document_data['document']

    # Load PDF data
    loader = OnlinePDFLoader(public_url)
    data = loader.load()
    
    # Split the text for analysis
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(data)

    doc_list = [t.page_content for t in texts]
    doc_content = "   ".join(doc_list) 

    return doc_content


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


def resume_parser(resume_text=None, document_id=None):
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
        instruction = get_resume_parser_instruction(section=section)
        response = get_openai_response(instruction, resume_text)
        resume_section_dict[section] = response
    
    return resume_section_dict


def extract_keywords_from_job_description(job_description):
    instruction = f"""Identify and list the keywords in the skills, technologies, qualifications sections that are relevant to the job. Job \
        description: {job_description}. Do not write any other text except from the keywords seperated with commas ",". Keywords are usually just one or two words.
    """
    response = get_openai_response(instruction, job_description)
    
    keywords = response.split(', ')
    return keywords


def keyword_analysis(resume_text, job_keywords):
    matching_keywords = []
    for keyword in job_keywords:
        if keyword.lower() in resume_text.lower():
            matching_keywords.append(keyword)
    
    matching_score = len(matching_keywords) / len(job_keywords)
    return matching_keywords, matching_score


def readability_analysis(resume_text):
    fk_score = textstat.flesch_kincaid_grade(resume_text)
    fre_score = textstat.flesch_reading_ease(resume_text)
    return fk_score, fre_score


def get_readability_text(fk_score, fre_score):
    feedback = ""
    if fk_score >= 12:
        feedback += f"- Your resume has a Flesch-Kincaid Grade Level of {fk_score}, indicating a collegiate reading level. Consider simplifying the language for broader accessibility.\n\n"
    else:
        feedback += f"- Your resume has a Flesch-Kincaid Grade Level of {fk_score}, indicating it's suitable for a wide range of readers. Good job!\n\n"
    
    if fre_score <= 60:
        feedback += f"- Your resume has a Flesch Reading Ease score of {fre_score}, which is considered difficult to read. Consider simplifying the language.\n\n"
    else:
        feedback += f"- Your resume has a Flesch Reading Ease score of {fre_score}, which is considered easy to read. Good job!\n\n"
    
    return feedback


def analyze_impact(text):
    instruction = "Identify and evaluate quantifiable achievements in the following text."
    response = get_openai_response(instruction, text)
    return response


def score_impact(achievements):
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
    score = sum(achievements[metric] * max_points[metric] for metric in achievements)
    return score


def score_job_role(role_description):
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
    response = get_openai_response(instruction, role_description)
    # Assume response contains scores for each metric
    return response


# Example usage
achievements = {
    'patient_outcomes': 0.8,
    'process_improvements': 0.7,
    'cost_management': 0.9,
    'team_management': 0.85,
    'certifications': 1.0,
    'patient_satisfaction': 0.95
}


def get_section_feedback(section_name, section_content):
    instruction = f"""
    You are a knowledgeable career advisor. Analyze the following content from the '{section_name}' section of a resume and provide constructive feedback:

    {section_content}
    """
    feedback = get_openai_response(instruction, section_content)
    return feedback


def provide_feedback(matching_keywords, missing_keywords, complexity_score, readability_score, section_feedback):
    feedback = "Feedback on your resume:\n\n"

    # Keyword Feedback
    feedback += "Keyword Matching:\n"
    feedback += f"- Matched Keywords: {', '.join(matching_keywords)}\n"
    feedback += f"- Missing Keywords: {', '.join(missing_keywords)}\n\n"

    # Readability Feedback
    feedback += "Readability:\n"
    feedback += get_readability_text(complexity_score, readability_score)
    
    # Section-wise Feedback
    feedback += "Section-wise Feedback:\n"
    for section, section_fb in section_feedback.items():
        feedback += f"- {section}: {section_fb}\n"

    return feedback


def optimize_resume(resume_content, job_description, resume_feedback):
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
    optimized_content = get_openai_response(instruction, content)
    return optimized_content


def main(resume_content, job_description):
    # 1. Parse the resume
    resume_section_dict = resume_parser(resume_text=resume_content)
    logger.info(f"----------------------- RESUME SECTION DICT -----------------------")
    logger.info(f"{resume_section_dict}")

    # 2. Extract keywords from the job description
    job_keywords = extract_keywords_from_job_description(job_description)
    logger.info(f"----------------------- JOB KEYWORDS -----------------------")
    logger.info(f"{job_keywords}")

    # 3. Perform analyses
    logger.info(f"----------------------- ANALYSIS -----------------------")
    matching_keywords, matching_score = keyword_analysis(resume_content, job_keywords)
    logger.info("------------ MATCHING KEYWORDS ------------")
    logger.info(f"{matching_keywords}")
    logger.info("------------ MATCHING SCORE ------------")
    logger.info(f"{matching_score}")
    complexity_score, readability_score = readability_analysis(resume_content)
    logger.info("------------ COMPLEXITY & READABILITY SCORE ------------")
    logger.info(f"{complexity_score, readability_score}")
    
    # 4. Provide feedback
    section_feedback = {}
    for section_name, section_content in resume_section_dict.items():
        section_feedback[section_name] = get_section_feedback(section_name, section_content)
    logger.info("----------------------- SECTION FEEDBACK -----------------------")
    logger.info(f"{section_feedback}")

    missing_keywords = [kw for kw in job_keywords if kw not in matching_keywords]
    logger.info("----------------------- MISSING KEYWORDS -----------------------")
    logger.info(f"{missing_keywords}")

    resume_feedback = provide_feedback(matching_keywords, missing_keywords, complexity_score, readability_score, section_feedback)
    
    # Output or return the feedback
    logger.info("----------------------- FULL RESUME FEEDBACK -----------------------")
    logger.info(f"{resume_feedback}")

    # ----------------------------------- OPTIMIZATION -----------------------------------
    logger.info("----------------------- OPTIMIZATION -----------------------")
    # return optimized resume output
    optimized_content = optimize_resume(resume_content, job_description, resume_feedback)
    logger.info("----------------------- FULL RESUME FEEDBACK -----------------------")
    logger.info(f"{optimized_content}")

    # 1. Parse the resume
    resume_section_dict = resume_parser(resume_text=optimized_content)
    logger.info(f"----------------------- RESUME SECTION DICT -----------------------")
    logger.info(f"{resume_section_dict}")

    # 3. Perform analyses
    logger.info(f"----------------------- ANALYSIS -----------------------")
    matching_keywords, matching_score = keyword_analysis(optimized_content, job_keywords)
    logger.info("------------ MATCHING KEYWORDS ------------")
    logger.info(f"{matching_keywords}")
    logger.info("------------ MATCHING SCORE ------------")
    logger.info(f"{matching_score}")
    complexity_score, readability_score = readability_analysis(optimized_content)
    logger.info("------------ COMPLEXITY & READABILITY SCORE ------------")
    logger.info(f"{complexity_score, readability_score}")


def run_main():
    main(resume_content, job_post_description)

# ------------------------ OTHER DOCS ------------------------
def cover_letter(cover_letter_content=None, document_id=None):
    # cover_letter_content = get_doc_data(document_id) 

    instruction = get_cover_letter_instruction(job_role="Backend Engineer")
    response = get_openai_response(instruction, cover_letter_content)
    print(response)
    return response


def job_post(document_id):
    job_post_content = get_doc_data(document_id) 

    instruction = get_job_post_instruction(job_role="Backend Engineer")
    response = get_openai_response(instruction, job_post_content)
    print(response)
    return response

# include candidate tone in optimization
# ----------------------- RESUME SECTION DICT -----------------------
{
    'Contact Information': 'Email: contactugodaniels@gmail.com | Phone: +2347033588400 | Location: Yaba, Lagos', 
    'Objective/Summary': '"Highly skilled Full Stack Developer and Software Engineer with a proven track record of developing and deploying innovative solutions. Proficient in Python, SQL, TensorFlow, and Keras. Experienced in developing e-commerce platforms, LMS, online tutoring websites, and integrating payment platforms, machine learning, and AI technologies."', 
    'Experience': '\n    EXPERIENCE\n\n    Gidaa | AI Developer                                    April 2023 - Present | Delaware, United States\n    Engineered an advanced AI application using Langchain, Pinecone (vector database), OpenAI ChatGPT API, and more. \n    Developed a customer assistant app to recommend tailored properties and mortgages, enhancing customer satisfaction.\n    Developed a customer assistant app to provide valuable information about the mortgage industry and simplified the mortgage application process for users. \n    Designed a risk assessment tool to categorize mortgage applicants based on spending and saving patterns.\n\n    Essential Recruit | AI Developer                    September 2023 - Present | Halifax, Canada\n    Created an AI application to recommend jobs to candidates using candidate data and preferences. \n    Developed AI application to assist candidates in optimizing resume, cover letters and recruiters in job post optimization.\n    Developed virtual assistant to provide guidance for candidates relocating to Canada for job opportunities. \n    Implemented AI application with note-taking capabilities during recruiter-candidate meetings/interviews.\n\n    Project School | Backend Developer                                            Feb 2023 | Lagos, Nigeria\n    Developed an LMS Platform serving 200+ students and 10 instructors with an 80% course completion rate.\n    Designed server-side architecture, reducing response times by 15% and improving stability.\n    Reduced feature integration time by 30% through reusable APIs, leading to a 20% increase in feature delivery speed.\n    Implemented API versioning, resulting in a 25% decrease in version mismatch errors.\n    Enhanced data accuracy with data validation rules, reducing data entry errors by 10%.\n    Created automated testing suites, increasing code coverage by 20% and reducing user-reported bugs by 15%.\n    Collaborated with front-end developers, reducing page load times by 25% and improving user satisfaction by 15%.\n    Ensured application security through robust protocols.\n    DFX Gadgets Hub | Full Stack Developer                                  Sep 2022 | Lagos, Nigeria\n    Increased sales by over 75% on the Ecommerce platform.\n    Integrated Stripe payment platform, increasing successful transactions by 10% and reducing support requests by 5%.\n    Optimized server-side architecture with Django, resulting in a 15% reduction in page load times and a 10% increase in user retention.\n    Improved API documentation and error handling, reducing support requests related to API usage by 20% and increasing user satisfaction.\n    Expanded third-party integrations, resulting in a 50% increase in integrations for users.\n    Reduced the average response time for database queries by 20%, improving overall application performance.\n    Enhanced application reliability, leading to a 20% decrease in crashes and downtime events.\n    Implemented third-party integrations, resulting in over 20% revenue increase.\n    Enhanced security measures, resulting in a 30% increase in customer retention and a 20% increase in new customer acquisition.\n\n    CyberMe Studio | Backend Developer           May 2022 – Sep 2022 | Riyadh, Saudi Arabia\n    Built a web scraper for Instagram data and a crypto trading bot for arbitrage opportunities, increasing revenue by 25%. \n    Designed algorithms to detect arbitrage in Centralized and Decentralized Exchanges, resulting in a 30% profit increase. \n    Utilized data collation systems and predictive models to boost profits by 15%.', 'Education': 'Yaba College of Technology | Higher National Diploma (Metallurgical Engineering) | Dec 2018 | Yaba, Lagos', 'Skills': 'Programming: Python, SQL, React, Kotlin \nTechnologies: TensorFlow, Keras, GCP, AWS, NumPy, Scikit-Learn, Pandas, OpenCV, Flask, Django, Brownie, Ethers.js, Hardhat, Weights & Biases, Langchain, Pinecone\nTools: Google Colaboratory, Jupyter Notebooks, Pycharm, Visual Studio, Git', 'Certifications': '\nDeepLearning.AI TensorFlow Developer Specialization \nMachine Learning, Object Localization with TensorFlow \nTransfer Learning for NLP with TensorFlow \nAdvanced Deployment Scenarios with TensorFlow \nNeural Networks and Deep Learning - AWS Machine Learning', 'Projects': "\nOne of my most rewarding projects was developing an AI-powered Mortgage Assistant at Giddaa, a Nigerian mortgage platform. Our goal was to democratize access to mortgages by creating a centralized platform offering diverse mortgage plans and flexible payment options.\n\nThe project aimed to leverage advanced technology to provide personalized mortgage recommendations, educate users about mortgages, and assess applicant risk profiles.\n\nWe employed Langchain for decentralization, Pinecone for vector databases, OpenAI ChatGPT API for natural language understanding, and machine learning for risk assessment.\n\nThe Mortgage Assistant delivers tailored mortgage and property recommendations to users, enhancing their ability to find suitable options.\nIt serves as an educational resource, explaining the mortgage industry and application process, empowering users to make informed choices.\nThe AI assesses applicant risk levels based on spending and saving patterns, offering insights to both applicants and mortgage providers.\nThis project has improved user experiences on Giddaa and supports the company's mission of increasing homeownership in Nigeria. It reaffirmed my passion for using technology to address real-world challenges and positively impact individuals and communities.", 
    'References': 'None'
}

# ----------------------- JOB KEYWORDS -----------------------
[
    'Python', 
    'SQL', 
    'Machine Learning', 
    'AI', 
    'LLM', 
    'Software Architecture', 
    'Code Reviews', 
    'AWS', 
    'Kubernetes', 
    'Django', 
    'PostgreSQL', 
    'Snowflake', 
    'ElasticSearch', 
    'dbt', 
    'Looker', 
    'scikit-learn', 
    'FastAPI', 
    'Celery', 
    'Jenkins', 
    'GitHub', 
    'ETL', 
    'Data Pipelines', 
    'Real-time notifications', 
    'Fraud prevention', 
    'Online Payments', 
    'Invoicing', 
    'Booking', 
    'Scoring algorithms', 
    'Software Engineering', 
    'English communication', 
    'Tech leadership', 
    'Mentoring', 
    'Data Engineering', 
    'SaaS', 
    'B2B', 
    'Proptech', 
    'API Development', 
    'Advanced Analytics', 
    'Coding Practices', 
    'Documentation', 
    'Unit testing', 
    'Integration testing', 
    'Data Quality', 
    'Security', 
    'Performance.'
]

# ----------------------- ANALYSIS -----------------------
# ------------ MATCHING KEYWORDS ------------
[
    'Python', 
    'SQL', 
    'Machine Learning', 
    'AI', 
    'AWS', 
    'Django', 
    'scikit-learn', 
    'Documentation', 
    'Security', 
    'Performance.'
]
# ------------ MATCHING SCORE ------------
0.2222222222222222
# ------------ READABILITY SCORE ------------
14.8
# ----------------------- SECTION FEEDBACK -----------------------
{
    'Contact Information': "This section looks well-formatted and clear - you've provided your email and phone number concisely, making it easy for potential employers to contact you. However, it might be better to use a more professional email address. Consider using your first and last name instead of 'ugodaniels'. For example, 'firstnamelastname@gmail.com' would come across more professional. Also, ensure that your phone number is accurate and that it is one where you can be easily reached. It's also a good thing that you've provided your location - just ensure this is relevant to the job you're applying for. All in all, great job, just a minor tweak to the email address would be perfect!", 
    'Objective/Summary': "Your resume's objective section is concise, clear, and highlights your major skills effectively. You effectively conveyed your proficiency in Python, SQL, TensorFlow, and Keras. Also, providing specific examples of projects, such as developing e-commerce platforms, LMS, online tutoring websites, and integrating payments, is beneficial. \n\nHowever, it would be more impactful if you can quantify some of your achievements, if possible. Metrics can make a resume stand out as recruiters will be more able to gauge the extent of your capabilities.\n\nAdditionally, rather than just stating that you have a proven track record, consider offering an example to illustrate this. For instance, did a solution you developed lead to certain improvements such as higher productivity, cost savings or another measurable benefit to the company?\n\nOther than these points, your objective is to-the-point and professional and outlines your broad range of software engineering skills.", 
    'Experience': 'Your resume gives a strong overall picture of your technical skills and ability to make a measurable impact at each role you\'ve held. Here are some areas where it could be improved:\n\n1. Results-Focused: It\'s great that you\'ve included clear metrics that demonstrate the impact of your work. You could further improve by providing more context for these metrics when possible. For example, what was the financial significance of the 75% sales increase at DFX Gadgets Hub?\n\n2. Redundancy: You mentioned "Developed a customer assistant app" twice in the Gidaa section. If these are the same app, combine these sentences into a single bullet point to maintain brevity. If they\'re different, consider differentiating them more.\n\n3. Transferable Skills: Don\'t forget about soft skills. While your technical skills are clear, you might want to highlight collaboration, leadership, or strategic thinking. You stated “Collaborated with front-end developers...” in Project School. Expand on this aspect.\n\n4. Overlapping Dates: The dates for your roles at Gidaa and Essential Recruit overlap. If you held these roles simultaneously, clarify this to avoid confusion.\n\n5. Action Verbs: Start each bullet point with a strong action verb. For example, "Implemented API versioning" rather than just "API versioning".\n\n6. Specific Technologies: It\'s excellent that you\'re mentioning the specific technologies you\'ve used, like Django and Stripe. Expand on this where possible, mentioning the specific technologies you\'ve used in other roles as well.\n\n7. Accomplishments Vs Duties: The resume primarily focuses on tasks you\'ve completed. Make it more compelling by highlighting major accomplishments or problems you\'ve solved.\n\nEnsure to tailor your experience to the job description, using keywords from the posting where appropriate. This can not only catch the employer\'s eye, but also help get your resume past applicant tracking systems.', 
    'Education': "The 'Education' section of your resume is clear, concise and informative. However, you could provide a little more detail to make it even better:\n\n1. Include the grades or GPA (if they are strong) to show your academic performance.\n2. You could also list any relevant coursework, projects, or thesis work you completed as part of your higher national diploma.\n3. If there were any special recognitions, awards, or scholarships during your educational tenure, then do mention those as well.\n\nRemember, providing specifics can help prospective employers understand the depth of your knowledge and experiences better.", 
    'Skills': 'This Skills section is very impressive as it demonstrates a wide range of skills across different areas. Here\'s a bit of feedback for improvement:\n\n1. Categorization: Whilst you have categorized your skills into programming, technologies, and tools, it might be more beneficial to categorize them according to the roles they are used for. For instance, Python, SQL, Tensorflow could be placed under "Data Analysis and Machine Learning" and React and Kotlin could go under "Web and Mobile Development".\n\n2. Proficiency Levels: It could help to mention your proficiency level for each of these skills, for instance, beginner, intermediate, or advanced. This gives employers a better idea of your strengths.\n\n3. Relevant Details: Adding brief details about where/how you used each of these technologies (specific projects, works) might make your resume more effectual.\n\n4. Order of Listing: Consider listing your skills starting from the most relevant to the job you\'re applying for, or the strongest ones. This can increase your resume\'s impact, as recruiters might not read a long list thoroughly.\n\nRemember, a resume is not just about listing your skills but also portraying them in a way that aligns with the job you\'re applying for.', 
    'Certifications': "This section of your resume is strong as it showcases a solid understanding of advanced data analysis techniques, such as machine learning and deep learning. It also reflects your proficiency with TensorFlow, a highly popular tool in this field, and AWS Machine Learning shows experience with cloud-based machine learning solutions, which is desirable in many industries.\n\nTo enhance this section, consider the following suggestions:\n1. While your certifications are impressive, mention if these were earned through comprehensive coursework or via a short-term study, as bulk of these certifications are provided by MOOCs that have varying timelines and depth of topics.\n2. Include the year you received each certification. This can help employers get a sense of how recent and relevant your knowledge is.\n3. If possible, specify the level of your certifications (foundation, professional, etc) if there is any to make it clear about your skill level.\n4. Reorder the certifications to provide a more logical narrative, like starting from basic/broad certifications to specific ones.\n5. You might like to link these certifications with the practical application, projects, or accomplishments made using these skills in the 'Experience' section of your resume.", 
    'Projects': 'Your projects section shows a hands-on experience with practical application of AI in the finance industry, which is a big plus. Including successful projects on your resume helps employers understand your capabilities and the impact you can make. Here are my advices for improvement:\n\n1. Quantifiable Results: While you have mentioned the AI assistant has improved user experience, it would be more impactful if you provide quantifiable results or metrics to back this up.\n\n2. Specific Roles: You should state your specific role and responsibilities in the project rather than using \'We\'. It\'s essential to demonstrate what you individually contributed to the project\'s success.\n\n3. Skills Used: Good that you\'ve mentioned several specific technologies used in the project. Consider listing these under a "Skills Used" subtitle to make it clearer and more readable.\n\n4. Challenge-Solution-Result format: The information can be better organized to follow a challenge-solution-result format. Start with the challenge or objective of the project, then the method or technology used for the solution and end with the result or impact created. This will create a more compelling story.\n\n5. Eliminate Jargons: The explanation of the technology used can be complex for non-tech-savvy recruiters or HR staff. Consider simplifying the language or providing a quick, understandable summary of how the technology was applied. For example, instead of saying, "We employed Langchain for decentralization, Pinecone for vector databases", you might say, "We used advanced technologies to securely store data and streamline the application process".\n\n6. User Benefits: It is clear the AI mortgage assistant has several features and capabilities, but it can make more of an impact if you speak to the benefit these features bring to the users. For instance, how the AI assistant’s ability to assess risk levels offers potential homeowners peace of mind and assurance.', 
    'References': 'The \'References\' section of a resume is important as it allows potential employers to contact former colleagues or employers to get a better understanding of your work habits, skills, and performance. By listing \'None\' it gives the impression you don\'t have previous employers, colleagues or even professors who can vouch for your abilities and work ethics. While it\'s acceptable to not include reference information directly on your resume, it may be better to indicate "References available upon request". However, the best approach would be to prepare a separate reference list to provide when requested by an employer.'
}

# ----------------------- MISSING KEYWORDS -----------------------
[
    'LLM', 
    'Software Architecture', 
    'Code Reviews', 
    'Kubernetes', 
    'PostgreSQL', 
    'Snowflake', 
    'ElasticSearch', 
    'dbt', 
    'Looker', 
    'FastAPI', 
    'Celery', 
    'Jenkins', 
    'GitHub', 
    'ETL', 
    'Data Pipelines', 
    'Real-time notifications', 
    'Fraud prevention', 
    'Online Payments', 
    'Invoicing', 
    'Booking', 
    'Scoring algorithms', 
    'Software Engineering', 
    'English communication', 
    'Tech leadership', 
    'Mentoring', 
    'Data Engineering', 
    'SaaS', 
    'B2B', 
    'Proptech', 
    'API Development', 
    'Advanced Analytics', 
    'Coding Practices', 
    'Unit testing', 
    'Integration testing', 
    'Data Quality'
]
# ----------------------- FINAL FEEDBACK -----------------------
"""Feedback on your resume:

Keyword Matching:
- Matched Keywords: Python, SQL, Machine Learning, AI, AWS, Django, scikit-learn, Documentation, Security, Performance.
- Missing Keywords: LLM, Software Architecture, Code Reviews, Kubernetes, PostgreSQL, Snowflake, ElasticSearch, dbt, Looker, FastAPI, Celery, Jenkins, GitHub, ETL, Data Pipelines, Real-time notifications, Fraud prevention, Online Payments, Invoicing, Booking, Scoring algorithms, Software Engineering, English communication, Tech leadership, Mentoring, Data Engineering, SaaS, B2B, Proptech, API Development, Advanced Analytics, Coding Practices, Unit testing, Integration testing, Data Quality

Readability:
- Your resume has a readability score of 14.8, which is considered difficult to read. Consider simplifying the language.

Section-wise Feedback:
- Contact Information: This section looks well-formatted and clear - you've provided your email and phone number concisely, making it easy for potential employers to contact you. However, it might be better to use a 
more professional email address. Consider using your first and last name instead of 'ugodaniels'. For example, 'firstnamelastname@gmail.com' would come across more professional. Also, ensure that your phone number is accurate and that it is one where you can be easily reached. It's also a good thing that you've provided your location - just ensure this is relevant to the job you're applying for. All in all, great job, just a minor tweak to the email address would be perfect!
- Objective/Summary: Your resume's objective section is concise, clear, and highlights your major skills effectively. You effectively conveyed your proficiency in Python, SQL, TensorFlow, and Keras. Also, providing specific examples of projects, such as developing e-commerce platforms, LMS, online tutoring websites, and integrating payments, is beneficial.

However, it would be more impactful if you can quantify some of your achievements, if possible. Metrics can make a resume stand out as recruiters will be more able to gauge the extent of your capabilities.

Additionally, rather than just stating that you have a proven track record, consider offering an example to illustrate this. For instance, did a solution you developed lead to certain improvements such as higher productivity, cost savings or another measurable benefit to the company?

Other than these points, your objective is to-the-point and professional and outlines your broad range of software engineering skills.
- Experience: Your resume gives a strong overall picture of your technical skills and ability to make a measurable impact at each role you've held. Here are some areas where it could be improved:

1. Results-Focused: It's great that you've included clear metrics that demonstrate the impact of your work. You could further improve by providing more context for these metrics when possible. For example, what was the financial significance of the 75% sales increase at DFX Gadgets Hub?

2. Redundancy: You mentioned "Developed a customer assistant app" twice in the Gidaa section. If these are the same app, combine these sentences into a single bullet point to maintain brevity. If they're different, consider differentiating them more.

3. Transferable Skills: Don't forget about soft skills. While your technical skills are clear, you might want to highlight collaboration, leadership, or strategic thinking. You stated “Collaborated with front-end developers...” in Project School. Expand on this aspect.

4. Overlapping Dates: The dates for your roles at Gidaa and Essential Recruit overlap. If you held these roles simultaneously, clarify this to avoid confusion.

5. Action Verbs: Start each bullet point with a strong action verb. For example, "Implemented API versioning" rather than just "API versioning".

6. Specific Technologies: It's excellent that you're mentioning the specific technologies you've used, like Django and Stripe. Expand on this where possible, mentioning the specific technologies you've used in other 
roles as well.

7. Accomplishments Vs Duties: The resume primarily focuses on tasks you've completed. Make it more compelling by highlighting major accomplishments or problems you've solved.

Ensure to tailor your experience to the job description, using keywords from the posting where appropriate. This can not only catch the employer's eye, but also help get your resume past applicant tracking systems.  
- Education: The 'Education' section of your resume is clear, concise and informative. However, you could provide a little more detail to make it even better:

1. Include the grades or GPA (if they are strong) to show your academic performance.
2. You could also list any relevant coursework, projects, or thesis work you completed as part of your higher national diploma.
3. If there were any special recognitions, awards, or scholarships during your educational tenure, then do mention those as well.

Remember, providing specifics can help prospective employers understand the depth of your knowledge and experiences better.
- Skills: This Skills section is very impressive as it demonstrates a wide range of skills across different areas. Here's a bit of feedback for improvement:

1. Categorization: Whilst you have categorized your skills into programming, technologies, and tools, it might be more beneficial to categorize them according to the roles they are used for. For instance, Python, SQL, Tensorflow could be placed under "Data Analysis and Machine Learning" and React and Kotlin could go under "Web and Mobile Development".

2. Proficiency Levels: It could help to mention your proficiency level for each of these skills, for instance, beginner, intermediate, or advanced. This gives employers a better idea of your strengths.

3. Relevant Details: Adding brief details about where/how you used each of these technologies (specific projects, works) might make your resume more effectual.

4. Order of Listing: Consider listing your skills starting from the most relevant to the job you're applying for, or the strongest ones. This can increase your resume's impact, as recruiters might not read a long list thoroughly.

Remember, a resume is not just about listing your skills but also portraying them in a way that aligns with the job you're applying for.
- Certifications: This section of your resume is strong as it showcases a solid understanding of advanced data analysis techniques, such as machine learning and deep learning. It also reflects your proficiency with TensorFlow, a highly popular tool in this field, and AWS Machine Learning shows experience with cloud-based machine learning solutions, which is desirable in many industries.

To enhance this section, consider the following suggestions:
1. While your certifications are impressive, mention if these were earned through comprehensive coursework or via a short-term study, as bulk of these certifications are provided by MOOCs that have varying timelines 
and depth of topics.
2. Include the year you received each certification. This can help employers get a sense of how recent and relevant your knowledge is.
3. If possible, specify the level of your certifications (foundation, professional, etc) if there is any to make it clear about your skill level.
4. Reorder the certifications to provide a more logical narrative, like starting from basic/broad certifications to specific ones.
5. You might like to link these certifications with the practical application, projects, or accomplishments made using these skills in the 'Experience' section of your resume.
- Projects: Your projects section shows a hands-on experience with practical application of AI in the finance industry, which is a big plus. Including successful projects on your resume helps employers understand your capabilities and the impact you can make. Here are my advices for improvement:

1. Quantifiable Results: While you have mentioned the AI assistant has improved user experience, it would be more impactful if you provide quantifiable results or metrics to back this up.

2. Specific Roles: You should state your specific role and responsibilities in the project rather than using 'We'. It's essential to demonstrate what you individually contributed to the project's success.

3. Skills Used: Good that you've mentioned several specific technologies used in the project. Consider listing these under a "Skills Used" subtitle to make it clearer and more readable.

4. Challenge-Solution-Result format: The information can be better organized to follow a challenge-solution-result format. Start with the challenge or objective of the project, then the method or technology used for 
the solution and end with the result or impact created. This will create a more compelling story.

5. Eliminate Jargons: The explanation of the technology used can be complex for non-tech-savvy recruiters or HR staff. Consider simplifying the language or providing a quick, understandable summary of how the technology was applied. For example, instead of saying, "We employed Langchain for decentralization, Pinecone for vector databases", you might say, "We used advanced technologies to securely store data and streamline the application process".

6. User Benefits: It is clear the AI mortgage assistant has several features and capabilities, but it can make more of an impact if you speak to the benefit these features bring to the users. For instance, how the AI assistant’s ability to assess risk levels offers potential homeowners peace of mind and assurance.
- References: The 'References' section of a resume is important as it allows potential employers to contact former colleagues or employers to get a better understanding of your work habits, skills, and performance. By listing 'None' it gives the impression you don't have previous employers, colleagues or even professors who can vouch for your abilities and work ethics. While it's acceptable to not include reference information directly on your resume, it may be better to indicate "References available upon request". However, the best approach would be to prepare a separate reference list to provide when requested by an employer.
"""