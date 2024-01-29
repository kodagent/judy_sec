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

    if doc_type == "CL":
        # Example of the desired JSON structure provided in the instruction
        example_structure = json.dumps(
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
                "body": "Letter Body",
                "concluding_greetings": "\n\nWarm regards,\nFull Name'",
            },
            indent=2,
        )

        # Structured instruction asking the model to format the response similarly
        structured_instruction = f"{instruction}\n\nHere is how I would like the information to be structured in JSON format:\n{example_structure}\n\nInclude line breaks where appropriate in all the sections of the letter. Now, based on the content provided above, please structure the document content accordingly."

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


async def check_grammar_and_spelling(text):
    logger.info(
        f"----------------------- GRAMMAR & SPELLING CORRECTIONS -----------------------"
    )

    spell = SpellChecker()
    misspelled = spell.unknown(text.split())
    corrections = {word: spell.correction(word) for word in misspelled}

    logger.info(f"{corrections}")

    return corrections


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


async def get_general_feedback_text(
    readability_feedback,
    polarity_feedback,
    tone_feedback,
):
    start_time = time.time()

    logger.info(f"----------------------- FEEDBACK -----------------------")
    feedback = readability_feedback

    feedback += f"\n\n{polarity_feedback}"

    feedback += f"\n\n{tone_feedback}"

    # logger.info(f"{feedback}")

    total = time.time() - start_time
    logger.info(f"Final Feedback Collation Time: {total}")

    return feedback


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
    # logger.info(f"{optimized_content}")

    total = time.time() - start_time
    logger.info(f"Improve Doc Response Time: {total}")
    return optimized_content


# =========================== PROP-UP FUNCTIONS ===========================


# =========================== TAILORING FUNCTIONS ===========================
async def match_keywords_func(doc_text, job_description):
    # Configure CountVectorizer to convert text to lowercase
    vectorizer = CountVectorizer(lowercase=True)

    # Fit the vectorizer to the job description to extract keywords
    vectorizer.fit([job_description])
    job_keywords = vectorizer.get_feature_names_out()

    # Tokenize the cover letter text to ensure accurate matching
    doc_text_words = set(doc_text.lower().split())

    # Find the intersection of job keywords and cover letter words
    matched_keywords = list(doc_text_words.intersection(job_keywords))

    # Optionally, calculate a matching score
    matching_score = len(matched_keywords) / len(job_keywords)

    return matched_keywords, matching_score


async def optimize_doc(doc_type, doc_text, job_description):
    logger.info("----------------------- OPTIMIZATION -----------------------")
    instruction = f"""
    Please provide an optimized version of the {doc_type} by Tailor this {doc_type} to fit job post.
    """

    content = f"""
    ORIGINAL CONTENT:
    {doc_text}

    JOB DESCRIPTION:
    {job_description}
    """

    optimized_content = await get_chat_response(instruction, content)

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
# =========================== DOCUMENT SAMPLES ===========================
