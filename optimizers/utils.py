import json
import time

import boto3
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


async def get_chat_response(instruction, message, doc_type=None):
    start_time = time.time()

    chat = ChatOpenAI(
        temperature=0.7,
        model_name="gpt-4-1106-preview",
        openai_api_key=settings.OPENAI_API_KEY,
    )

    messages = [SystemMessage(content=instruction), HumanMessage(content=message)]

    if doc_type:
        if doc_type == "CL":
            structured_instruction = f"{instruction}\n\nHere is how I would like the information to be structured in JSON format:\n{cover_letter_example_structure}\n\nInclude line breaks where appropriate in all the sections of the letter. Now, based on the content provided above, please structure the document content accordingly."
        elif doc_type == "R":
            structured_instruction = f"{instruction}\n\nHere is how I would like the information to be structured in JSON format:\n{resume_example_structure}\n\nIf there isn't any provided value for the required key in the json format, return None as corresponding value.\nInclude line breaks where appropriate in all the sections of the letter. Now, based on the content provided above, please structure the document content accordingly."
        elif doc_type == "R-sections-fb":
            structured_instruction = f"{instruction}\n\nHere is how I would like the information to be structured in JSON format:\n{resume_fb_example_structure}\n\nDo not miss any key value pair when creating the JSON data."

        messages = [
            {"role": "system", "content": structured_instruction},
            {"role": "user", "content": message},
        ]

        structured_response = await client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            response_format={"type": "json_object"},
        )

        response = json.loads(structured_response.choices[0].message.content)

        total = time.time() - start_time
        logger.info(f"Chat Response Time: {total}")

        return response

    response = chat(messages).content

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


async def get_job_post_feedback(doc_text):
    start_time = time.time()

    logger.info(f"----------------------- JOB POST REVIEW -----------------------")

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

    job_post_feedback = await get_chat_response(instruction, doc_text)

    logger.info(f"{job_post_feedback}")

    total = time.time() - start_time
    logger.info(f"Job Post Review Time: {total}")
    return job_post_feedback


async def create_doc(doc_type_1, doc_type_2, doc_content, default_doc):
    start_time = time.time()

    logger.info("----------------------- DOC CREATION -----------------------")

    instruction = f"""
    Create a generic {doc_type_1} using the {doc_type_2} provided. 
    """

    content = f"""
    {doc_type_2.upper()} PROVIDED:
    {doc_content}

    DOC SAMPLE: 
    {default_doc}
    """

    created_content = await get_chat_response(instruction, content, doc_type="CL")

    logger.info(
        f"----------------------- CREATED {doc_type_1.upper()} -----------------------"
    )
    logger.info(f"{created_content}")

    total = time.time() - start_time
    logger.info(f"Doc Creation Response Time: {total}")
    return created_content


async def improve_doc(doc_type, doc_content, doc_feedback):
    """Optimizes a document based on its type and provided feedback.

    Args:
        doc_type (str): The type of the document (e.g., 'cover letter', 'resume', 'job post').
        content (str): The original content of the document.
        feedback (str, optional): Feedback provided for optimization. Defaults to None.

    Returns:
        str: The optimized content.
    """

    start_time = time.time()
    doc_type_upper = doc_type.upper()
    logger.info(
        f"----------------------- {doc_type_upper} OPTIMIZATION STARTED -----------------------"
    )

    instruction_base = f"Provide an optimized version of the {doc_type}."
    if doc_feedback:
        instruction = f"{instruction_base} Use the feedback provided and ensure not to miss out on any part of the document"
        content_feedback_combined = f"ORIGINAL CONTENT:\n{doc_content}\n\n{doc_type_upper} FEEDBACK:\n{doc_feedback}"
    else:
        instruction = (
            f"{instruction_base} Ensure not to miss out on any part of the document."
        )
        content_feedback_combined = f"ORIGINAL CONTENT:\n{doc_content}"

    if doc_type == "cover letter":
        optimized_content = await get_chat_response(
            instruction, content_feedback_combined, doc_type="CL"
        )
    elif doc_type == "resume":
        optimized_content = await get_chat_response(
            instruction, content_feedback_combined, doc_type="R"
        )
    elif doc_type == "job post":
        optimized_content = await get_chat_response(
            instruction, content_feedback_combined
        )

    logger.info(
        f"----------------------- FULL {doc_type_upper} FEEDBACK -----------------------"
    )
    logger.info(f"{optimized_content}")

    total = time.time() - start_time
    logger.info(f"Improved Doc Response Time: {total}")
    return optimized_content


async def customize_doc(doc_type, doc_content, custom_instruction):
    start_time = time.time()

    logger.info("----------------------- OPTIMIZATION -----------------------")

    instruction = f"""
    Make adjustments to the {doc_type} using the adjustment instruction provided. 
    """

    content = f"""
    ORIGINAL CONTENT:
    {doc_content}

    {doc_type.upper()} ADJUSTMENT INSTRUCTION:
    {custom_instruction}
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
    # logger.info(f"{optimized_content}")
    return optimized_content


# =========================== TAILORING FUNCTIONS ===========================


# =========================== DATABASE FUNCTIONS ===========================
def upload_directly_to_s3(file, bucket_name, s3_key):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        # region_name='your-region',  # Uncomment and set your region if necessary
    )

    # Include ExtraArgs to set content type and content disposition
    s3.upload_fileobj(
        file,
        bucket_name,
        s3_key,
        ExtraArgs={
            "ContentType": "application/pdf",
            "ContentDisposition": "inline",
        },
    )


def get_full_url(s3_key):
    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"


# =========================== DATABASE FUNCTIONS ===========================
