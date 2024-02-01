import json
import time

import textstat as textstat_analysis
from django.conf import settings
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from sklearn.feature_extraction.text import CountVectorizer
from spellchecker import SpellChecker
from textblob import TextBlob

from chatbackend.configs.base_config import openai_client as client
from chatbackend.configs.logging_config import configure_logger

logger = configure_logger(__name__)

SYSTEM_ROLE = "system"
USER_ROLE = "user"


cover_letter_example_structure = json.dumps(
    {
        # "sender_info": {
        #     "name": "Sender Name",
        #     "address": "Sender Address",
        #     "phone": "Sender Phone",
        #     "email": "Sender Email",
        #     "date": "Letter Date",
        # },
        # "recipient_info": {
        #     "name": "Recipient Name",
        #     "address": "Recipient Address",
        # },
        "body": "Letter Body excluding concluding greetings like 'Warm regards,\nFull Name'",
        "concluding_greetings": "\n\nWarm regards,\nFull Name'",
    },
    indent=2,
)


resume_fb_example_structure = json.dumps(
    {
        "contact": "Feedback on contact section",
        "summary": "Feedback on summary section",
        "experiences": {
            "experience_1": "Feedback on first experience section",
            "experience_2": "Feedback on second experience section",
            "experience_3": "Feedback on third experience section",
            # Additional education entries can be added here
        },
        "education": [
            "Feedback on first education section",
            # Additional education entries can be added here
        ],
        "skills": "Feedback on skills section",
        "certifications": [
            "Feedback on certifications section",
            # Additional certifications can be listed here
        ],
        # "projects": [
        #     "Feedback on projects section",
        #     # Additional projects can be listed here
        # ],
        "references": [
            "Feedback on references section",
            # Additional references can be added here
        ],
    },
    indent=2,
)


resume_example_structure = json.dumps(
    {
        "contact": {
            "name": "Sender Name",
            "address": "Sender Address",
            "phone": "Sender Phone",
            "email": "Sender Email",
            "linkedIn": "LinkedIn Profile url (if available)",
        },
        "summary": "Resume Executive Summary",
        "experiences": {
            "experience_1": {
                "company_name": "Name of company worked for",
                "job_role": "Job Position",
                "start_date": "Start date of job",
                "end_date": "End date of job if available",
                "location": "Location of the company",
                "job_description": [
                    "First Description of Job Responsibilities and Achievements",
                    "Second Description of Job Responsibilities and Achievements",
                    "Third Description of Job Responsibilities and Achievements",
                    # Additional descriptions can be added here
                ],
            },
            "experience_2": {
                "job_title": "Job Position",
                "start_date": "Start date of job",
                "end_date": "End date of job if available",
                "job_description": "Description of Job Responsibilities and Achievements",
            },
            "experience_3": {
                "job_title": "Job Position",
                "start_date": "Start date of job",
                "end_date": "End date of job if available",
                "job_description": "Description of Job Responsibilities and Achievements",
            },
        },
        "education": [
            {
                "institution": "Educational Institution",
                "degree": "Degree Obtained",
                "end_date": "End Date",
                "location": "Location of institution",
                "details": "Details about the Course or Achievements if available",
            },
            # Additional education entries can be added here
        ],
        "skills": [
            "Skill 1",
            "Skill 2",
            # Additional skills can be listed here
        ],
        "certifications": [
            {
                "title": "Certification Title",
                "issuing_organization": "Issuing Organization",
                "date_obtained": "Date Obtained (if applicable)",
                "validity_period": "Validity Period (if applicable)",
            },
            # Additional certifications can be listed here
        ],
        # "projects": [
        #     {
        #         "project_title": "Project Title",
        #         "duration": "Project Duration",
        #         "description": "Project Description",
        #         "technologies_used": ["Technology 1", "Technology 2"],
        #     },
        #     # Additional projects can be listed here
        # ],
        "references": [
            {
                "referee_name": "Referee Name",
                "relationship": "Relationship to the Referee",
                "contact_information": "Referee Contact Information",
            },
            # Additional references can be added here
        ],
    },
    indent=2,
)


job_post_keywords_example_structure = json.dumps(
    {"keywords": "List of keywords"},
    indent=2,
)


async def get_openai_response(INSTRUCTION, content, functions=None, function_name=None):
    """
    This function is used for getting responses when there is a need for function call otherwise use get_chat_response
    """
    messages = [
        {"role": SYSTEM_ROLE, "content": INSTRUCTION},
        {"role": USER_ROLE, "content": content},
    ]

    if functions:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            functions=functions,
            function_call={"name": function_name},
        )
        return response["choices"][0]["message"]
    else:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
        )

        return response.choices[0].message.content


async def get_chat_response(instruction, message, doc_type=None):
    start_time = time.time()

    chat = ChatOpenAI(
        temperature=0.7,
        model_name="gpt-4-1106-preview",
        openai_api_key=settings.OPENAI_API_KEY,
    )

    messages = [SystemMessage(content=instruction), HumanMessage(content=message)]

    response = chat(messages).content

    if doc_type:
        if doc_type == "CL":
            structured_instruction = f"{instruction}\n\nHere is how I would like the information to be structured in JSON format:\n{cover_letter_example_structure}\n\nInclude line breaks where appropriate in all the sections of the letter. Now, based on the content provided above, please structure the document content accordingly."
        elif doc_type == "R":
            structured_instruction = f"{instruction}\n\nHere is how I would like the information to be structured in JSON format:\n{resume_example_structure}\n\nInclude line breaks where appropriate in all the sections of the letter. Now, based on the content provided above, please structure the document content accordingly."
        elif doc_type == "R-sections-fb":
            structured_instruction = f"{instruction}\n\nHere is how I would like the information to be structured in JSON format:\n{resume_fb_example_structure}"

        messages = [
            {"role": "system", "content": structured_instruction},
            {"role": "user", "content": message},
        ]

        structured_response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            response_format={"type": "json_object"},
        )

        response = json.loads(structured_response.choices[0].message.content)

    total = time.time() - start_time
    logger.info(f"Chat Response Time: {total}")
    return response


# =========================== PROP-UP FUNCTIONS ===========================
class Readablity:
    def __init__(self, text):
        self.text = text

    async def analyze_readability(self):
        self.complexity_score = textstat_analysis.flesch_kincaid_grade(self.text)
        self.readability_score = textstat_analysis.flesch_reading_ease(self.text)
        return self.complexity_score, self.readability_score

    async def get_readability_text(self, doc_type):
        start_time = time.time()
        await self.analyze_readability()

        feedback = "Readability:\n"
        if self.complexity_score >= 12:
            feedback += f"- Your {doc_type} has a Flesch-Kincaid Grade Level of {self.complexity_score}, indicating a collegiate reading level. Consider simplifying the language for broader accessibility.\n\n"
        else:
            feedback += f"- Your {doc_type} has a Flesch-Kincaid Grade Level of {self.complexity_score}, indicating it's suitable for a wide range of readers. Good job!\n\n"

        if self.readability_score <= 60:
            feedback += f"- Your {doc_type} has a Flesch Reading Ease score of {self.readability_score}, which is considered difficult to read. Consider simplifying the language.\n\n"
        else:
            feedback += f"- Your {doc_type} has a Flesch Reading Ease score of {self.readability_score}, which is considered easy to read. Good job!\n\n"

        total = time.time() - start_time
        logger.info(f"Readability Response Time: {total}")

        return feedback


class Polarity:
    def __init__(self, text):
        self.text = text

    async def analyze_sentiment(self):
        logger.info(f"----------------------- TONE (POLARITY) -----------------------")

        analysis = TextBlob(self.text)
        self.polarity = analysis.sentiment.polarity

        # logger.info(f"{self.polarity}")

        return self.polarity

    async def get_polarity_text(self, doc_type):
        start_time = time.time()

        await self.analyze_sentiment()
        feedback = "Sentiment Analysis:\n"
        if self.polarity < 0:
            feedback += f"- The tone of your {doc_type} is more negative (polarity: {self.polarity}). Consider revising to convey a more positive or neutral tone.\n\n"
        else:
            feedback += f"- The tone of your {doc_type} is positive or neutral (polarity: {self.polarity}). Good job!\n\n"

        total = time.time() - start_time
        logger.info(f"Polarity Response Time: {total}")

        return feedback


async def check_grammar_and_spelling(text):
    logger.info(
        f"----------------------- GRAMMAR & SPELLING CORRECTIONS -----------------------"
    )

    spell = SpellChecker()
    misspelled = spell.unknown(text.split())
    corrections = {word: spell.correction(word) for word in misspelled}

    logger.info(f"{corrections}")

    return corrections


async def review_tone(doc_type, text):
    start_time = time.time()

    logger.info(f"----------------------- TONE REVIEW -----------------------")

    instruction = f"""
    Review the following {doc_type} based on professionalism, assertiveness, and compassion:

    Provide feedback on each of these aspects.
    """
    tone_feedback = await get_chat_response(instruction, text)

    feedback_title = "Tone Review:\n"
    final_feedback = feedback_title + tone_feedback

    # logger.info(ff"{final_feedback}")

    total = time.time() - start_time
    logger.info(f"Tone Review Response Time: {total}")
    return final_feedback


async def resume_sections_feedback(doc_text):
    start_time = time.time()

    logger.info(
        f"----------------------- RESUME SECTIONS REVIEW -----------------------"
    )

    instruction = f"""
    You are a professional recruiter. Review each resume section based on professionalism, assertiveness, compassion and impact where necessary and provide constructive feedback to help in improving the resume:
    """

    resume_feedback = await get_chat_response(
        instruction, doc_text, doc_type="R-sections-fb"
    )

    feedback_title = "RESUME Review:\n"
    final_feedback = feedback_title + json.dumps(resume_feedback)

    logger.info(f"{final_feedback}")

    total = time.time() - start_time
    logger.info(f"Resume Review Response Time: {total}")
    return final_feedback


async def improve_doc(doc_type, doc_content, doc_feedback):
    start_time = time.time()

    logger.info("----------------------- OPTIMIZATION -----------------------")

    instruction = f"""
    Please provide an optimized version of the {doc_type} using the feedback provided. 
    """

    content = f"""
    ORIGINAL CONTENT:
    {doc_content}

    {doc_type.upper()} FEEDBACK:
    {doc_feedback}
    """

    if doc_type == "cover letter":
        optimized_content = await get_chat_response(instruction, content, doc_type="CL")
    elif doc_type == "resume":
        optimized_content = await get_chat_response(instruction, content, doc_type="R")

    logger.info(
        f"----------------------- FULL {doc_type.upper()} FEEDBACK -----------------------"
    )
    logger.info(f"{optimized_content}")

    total = time.time() - start_time
    logger.info(f"Improved Doc Response Time: {total}")
    return optimized_content


# =========================== PROP-UP FUNCTIONS ===========================


# =========================== RESUME FUNCTIONS ===========================
# async def parse_rresume():
#     logger.info("----------------------- RESUME PARSING -----------------------")

#     instruction = f"""
#         You are a helper assistant that helps with detailed resume parsing. Extract and return only the text in the resume. Do not write any additional text\
#         Take a look at the content of this resume and extract the contents of section: {section}. if section doesn't exist return None
#     """

#     content = f"""
#     ORIGINAL CONTENT:
#     {doc_content}

#     {doc_type.upper()} FEEDBACK:
#     {doc_feedback}
#     """
#     get_chat_response
#     pass


# use this when optimizing JP and save result to DB
async def extract_keywords(job_description):
    instruction = f"""Identify and list the keywords in the skills, technologies, qualifications sections that are relevant to the job. Job \
        description: {job_description}. Do not write any other text except from the keywords seperated with commas ",". Keywords are usually just one or two words.
    """

    keywords = await get_chat_response(
        instruction, job_description, doc_type="JP-keywords"
    )
    keywords = keywords.split(", ")
    return keywords


# =========================== RESUME FUNCTIONS ===========================


# =========================== TAILORING FUNCTIONS ===========================
async def keyword_analysis1(doc_text_1, doc_text_2):
    # Configure CountVectorizer to convert text to lowercase
    vectorizer = CountVectorizer(lowercase=True)

    # Fit the vectorizer to the second doc to extract keywords. E.g Job description
    vectorizer.fit([doc_text_2])
    doc_text_2_keywords = vectorizer.get_feature_names_out()

    # Tokenize the first text text to ensure accurate matching. E.g Resume
    doc_text_1_words = set(doc_text_1.lower().split())

    # Find the intersection of extracted keywords and doc text words
    matched_keywords = list(doc_text_1_words.intersection(doc_text_2_keywords))

    # Optionally, calculate a matching score
    matching_score = len(matched_keywords) / len(doc_text_2_keywords)

    return matched_keywords, matching_score


# Might not be required
# async def keyword_analysis1(doc_text, job_keywords):
#     matching_keywords = []
#     for keyword in job_keywords:
#         if keyword.lower() in doc_text.lower():
#             matching_keywords.append(keyword)

#     matching_score = len(matching_keywords) / len(job_keywords)
#     return matching_keywords, matching_score


async def optimize_doc(doc_type, doc_text, job_description):
    logger.info("----------------------- OPTIMIZATION -----------------------")
    instruction = f"""
        You are a professional recruiter that helps individuals optimize their {doc_type}. \
        Please provide an optimized version of the {doc_type} by tailoring it to fit job post.
    """

    content = f"""
    ORIGINAL CONTENT:
    {doc_text}

    JOB DESCRIPTION:
    {job_description}
    """

    if doc_type == "cover letter":
        optimized_content = await get_chat_response(instruction, content, doc_type="CL")
    elif doc_type == "resume":
        optimized_content = await get_chat_response(instruction, content, doc_type="R")

    logger.info(
        f"----------------------- {doc_type.upper()} TAILORED -----------------------"
    )
    logger.info(f"{optimized_content}")
    return optimized_content


# =========================== TAILORING FUNCTIONS ===========================


# =========================== DOCUMENT SAMPLES ===========================
default_cover_letter = """
Dear Hiring Manager,

I am thrilled to apply for the Registered Nurse (RN) - Acute Care position at St. Mary's Health Centre. With my strong background in acute care nursing and a deep commitment to patient-focused care, I am eager to contribute to your team's esteemed reputation for empathetic service and clinical excellence. 
As a dedicated RN with a Bachelor of Science in Nursing from the Toronto School of Health Sciences and over three years of experience in high-pressure acute care settings, I have honed a robust skill set that aligns with the demands of St. Mary's fast-paced environment. My current role at Good Health Hospital in Toronto has equipped me to excel in situations that require swift decision-making, precise assessments, and the execution of intricate treatment plans.

Key achievements in my professional journey include:
1. Effective management of patients with diverse and complex health conditions, ensuring compassionate and proficient treatment.
2. Demonstrating a strong ability to work collaboratively with cross-functional health care teams to enhance patient care plans and outcomes.
3. Advocacy for patient education, ensuring comprehensible discharge processes, which has notably decreased readmission rates.
4. Maintaining diligent documentation practices, thereby enhancing the accuracy and reliability of patient records.

The holistic approach to health care at St. Mary's Health Centre and its emphasis on continuous professional development resonate with me. The prospect of working within an institution that offers a supportive work environment and values staff well-being is highly appealing to me.

Attached is my resume for your review. I am eager to discuss how my clinical expertise and personal ethos can align with the noble mission of St. Mary's Health Centre. Please feel free to contact me at your earliest convenience by phone at (647) 555-0198 or via email at emily.johnson@fakemail.com.

Thank you for considering my application. I am confident in my ability to make a meaningful contribution to your distinguished team and am excited about the opportunity to bring my dedication and skills to your institution.

Warm regards,
Emily Johnson 
"""


default_resume = """
DANIEL NWACHUKWU
Email: contactugodaniels@gmail.com | Phone: +2347033588400 | Location: Yaba, Lagos

SUMMARY
Software Engineer with over 4 years of professional experience in developing and deploying innovative solutions, with a strong interest in Machine Learning and AI. Known for developing ML/AI-powered applications. Fluent in English, with excellent problem-solving skills and the ability to think outside the box.

EXPERIENCE
Gidaa | AI Developer                                    April 2023 - Present | Delaware, United States
Engineered advanced recommendation system to tailor properties and mortgage plans to users on the platform thereby increasing customer satisfaction by 25%. 
Led the development of a customer guide feature to simplify the mortgage application process for users and provide valuable information about the mortgage industry increasing ease of use by 40%.
Created a risk assessment tool to categorize mortgage plan applicants based on spending and saving patterns increasing the candidate analysis process by 30%.

Essential Recruit | AI Developer                    September 2023 - Present | Halifax, Canada
Developed an AI application for job recommendations, to candidates using candidate data and preferences pushing up job acquisition rate by 60%.
Developed AI tool for resume optimization, cover letters optimization, job post optimization, catering to over 500 candidates and recruiters.
Developed virtual assistant to provide relocation guidance for candidates 
Implemented AI note-taking plugin integratable for interview meetings. Used in over 10 interview calls weekly.

Project School | Backend Developer                                            Feb 2023 | Lagos, Nigeria
Improved server-side architecture and built reusable APIs, quickening the response times by 20%.
Implemented API versioning, cutting down version mismatch errors by 25%.
Enhanced data accuracy with data validation rules, reducing data entry errors by 10%.
Created automated testing suites, increasing code coverage by 20% and reducing user-reported bugs by 15%.
Collaborated with front-end developers, reducing page load times by 25% and improving user satisfaction by 15%.
Ensured application security through robust protocols.

DFX Gadgets Hub | Full Stack Developer                                  Sep 2022 | Lagos, Nigeria
Boosted sales by over 75% on the Ecommerce platform and reduced support requests by 5%.
Updated server-side architecture, resulting in a 15% reduction in page load times and a 10% increase in user retention.
Improved API documentation and error handling, reducing support requests related to API usage by 20%.
Expanded third-party integrations, resulting in a 50% increase in integrations for users.
Integrated Stripe payment platform, increasing successful transactions by 10% and reducing support requests by 5%.
Reduced the average response time for database queries by 20%, improving overall application performance.
Enhanced security measures, resulting in a 30% increase in customer retention and a 20% increase in new customer acquisition.

CyberMe Studio | Backend Developer           May 2022 – Sep 2022 | Riyadh, Saudi Arabia
Developed a web scraper for Instagram data and a trading bot, resulting in a 25% increase in revenue.
Designed algorithms for arbitrage detection in Centralized and Decentralized Exchanges, boosting profits by 30%. 
Implemented data collation systems and predictive models to growing profits by 15%.

EDUCATION
Yaba College of Technology | Higher National Diploma (Metallurgical Engineering) | Dec 2018 | Yaba, Lagos

TECHNICAL SKILLS 
Python (Advanced), SQL (Advanced), React (Intermediate), Kotlin (Beginner)
Machine Learning Libraries: TensorFlow (Advanced), Keras (Advanced), Scikit-Learn (Advanced)
Cloud Technologies: AWS, GCP
Web Development: Flask, Django
Blockchain/Smart Contract Tools: Brownie, Ethers.js, Hardhat
Data Analysis Libraries: NumPy, Pandas
IDEs and Version Control: Google Colaboratory, Jupyter Notebooks, Pycharm, Visual Studio, Git

CERTIFICATIONS 
DeepLearning.AI TensorFlow Developer Specialization 
Machine Learning, Object Localization with TensorFlow 
Transfer Learning for NLP with TensorFlow 
Advanced Deployment Scenarios with TensorFlow 
Neural Networks and Deep Learning - AWS Machine Learning

REFERENCES 
Available upon request.

LinkedIn Profile: https://www.linkedin.com/in/ugo-nwachukwu
"""
# =========================== DOCUMENT SAMPLES ===========================
