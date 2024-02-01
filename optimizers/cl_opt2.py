import asyncio
import time

from asgiref.sync import sync_to_async
from django.conf import settings
from django.shortcuts import get_object_or_404
from sklearn.feature_extraction.text import CountVectorizer
from spellchecker import SpellChecker
from textblob import TextBlob

from chatbackend.configs.logging_config import configure_logger
from helpers.optimizer_utils import cover_letter, job_post_description
from optimizers.mg_database import get_cover_letter_content, get_job_post_content_async
from optimizers.models import Analysis, CoverLetter, JobPost, OptimizedContent
from optimizers.utils import (
    analyze_readability,
    get_chat_response,
    get_readability_text,
    match_keywords_func,
)

logger = configure_logger(__name__)

SYSTEM_ROLE = "system"
USER_ROLE = "user"


async def check_grammar_and_spelling(text):
    logger.info(
        f"----------------------- GRAMMAR & SPELLING CORRECTIONS -----------------------"
    )

    spell = SpellChecker()
    misspelled = spell.unknown(text.split())
    corrections = {word: spell.correction(word) for word in misspelled}

    logger.info(f"{corrections}")

    return corrections


async def analyze_sentiment(cover_letter):
    logger.info(f"----------------------- TONE (POLARITY) -----------------------")

    analysis = TextBlob(cover_letter)
    polarity = analysis.sentiment.polarity

    logger.info(f"{polarity}")

    return polarity


async def review_tone(cover_letter_text):
    logger.info(f"----------------------- TONE REVIEW -----------------------")

    instruction = f"""
    Review the following cover letter based on professionalism, assertiveness, and compassion:

    Provide feedback on each of these aspects.
    """
    tone_feedback = await get_chat_response(instruction, cover_letter_text)

    logger.info(f"{tone_feedback}")
    return tone_feedback


async def get_feedback_text(
    matched_keywords,
    matching_score,
    complexity_score,
    readability_score,
    polarity,
    tone_feedback,
):
    logger.info(f"----------------------- FEEDBACK -----------------------")
    feedback = ""

    # # Grammar and Spelling Feedback
    # if corrections:
    #     feedback += "Grammar & Spelling Corrections:\n"
    #     for incorrect, correct in corrections.items():
    #         feedback += f"- Incorrect: {incorrect}, Suggested Correction: {correct}\n"
    #     feedback += "\n"

    # Keywords Matching Feedback
    feedback += "Keyword Matching:\n"
    feedback += f"- Matched Keywords: {', '.join(matched_keywords)}\n"
    feedback += f"- Matching Score: {matching_score*100:.2f}%\n\n"

    # Readability Feedback
    feedback += "Readability:\n"
    if complexity_score >= 12:
        feedback += f"- Your cover letter has a Flesch-Kincaid Grade Level of {complexity_score}, indicating a collegiate reading level. Consider simplifying the language for broader accessibility.\n"
    else:
        feedback += f"- Your cover letter has a Flesch-Kincaid Grade Level of {complexity_score}, indicating it's suitable for a wide range of readers. Good job!\n"

    if readability_score <= 60:
        feedback += f"- Your cover letter has a Flesch Reading Ease score of {readability_score}, which is considered difficult to read. Consider simplifying the language.\n\n"
    else:
        feedback += f"- Your cover letter has a Flesch Reading Ease score of {readability_score}, which is considered easy to read. Good job!\n\n"

    # Sentiment Analysis Feedback
    feedback += "Sentiment Analysis:\n"
    if polarity < 0:
        feedback += f"- The tone of your cover letter is more negative (polarity: {polarity}). Consider revising to convey a more positive or neutral tone.\n\n"
    else:
        feedback += f"- The tone of your cover letter is positive or neutral (polarity: {polarity}). Good job!\n\n"

    # Custom Tone Review Feedback
    feedback += "Tone Review:\n"
    feedback += f"{tone_feedback}\n"

    logger.info(f"{feedback}")
    return feedback


async def optimize_cover_letter(
    cover_letter_content, job_description, cover_letter_feedback
):
    logger.info("----------------------- OPTIMIZATION -----------------------")
    instruction = f"""
    Please provide an optimized version of the cover letter using the feedback provided. Do not add any extra text, just the cover letter.
    """

    content = f"""
    ORIGINAL CONTENT:
    {cover_letter_content}

    JOB DESCRIPTION:
    {job_description}

    COVER LETTER FEEDBACK:
    {cover_letter_feedback}
    """
    optimized_content = await get_chat_response(instruction, content)
    logger.info("----------------------- FULL RESUME FEEDBACK -----------------------")
    logger.info(f"{optimized_content}")
    return optimized_content


async def run_cover_letter_optimization(application_id, job_post_id):
    start_time = time.time()
    # Get the document content
    cover_letter_content, job_post_content = await asyncio.gather(
        get_cover_letter_content(application_id),
        get_job_post_content_async(job_post_id),
    )

    # Prepare the synchronous calls to be awaited
    job_post_update = sync_to_async(
        JobPost.objects.update_or_create, thread_sensitive=True
    )
    cover_letter_update = sync_to_async(
        CoverLetter.objects.update_or_create, thread_sensitive=True
    )

    # Run the synchronous database update_or_create functions concurrently
    job_post_instance, job_post_created = await job_post_update(
        job_post_id=job_post_id,
        defaults={"title": f"job-post-{job_post_id}", "description": job_post_content},
    )

    cover_letter_instance, cover_letter_created = await cover_letter_update(
        cover_letter_id=application_id,
        defaults={"content": cover_letter_content, "job_post": job_post_instance},
    )

    (
        corrections,
        polarity,
        tone_feedback,
        (matched_keywords, matching_score),
        (complexity_score, readability_score),
    ) = await asyncio.gather(
        check_grammar_and_spelling(cover_letter_content),
        analyze_sentiment(cover_letter_content),
        review_tone(cover_letter_content),
        match_keywords_func(cover_letter_content, job_post_content),
        analyze_readability(cover_letter_content),
    )

    feedback, cover_letter_feedback = await asyncio.gather(
        get_readability_text(complexity_score, readability_score),
        get_feedback_text(
            matched_keywords,
            matching_score,
            complexity_score,
            readability_score,
            polarity,
            tone_feedback,
        ),
    )

    optimized_content = await optimize_cover_letter(
        cover_letter_content, job_post_content, cover_letter_feedback
    )

    # Prepare the synchronous calls to be awaited
    analysis_update = sync_to_async(
        Analysis.objects.update_or_create, thread_sensitive=True
    )
    optimized_content_update = sync_to_async(
        OptimizedContent.objects.update_or_create, thread_sensitive=True
    )

    # Run the synchronous database update_or_create functions concurrently
    analysis_instance, analysis_created = await analysis_update(
        cover_letter=cover_letter_instance,
        job_post=job_post_instance,
        defaults={
            "keyword_matches": matched_keywords,
            "readability_score": readability_score,
            # ... other analysis data fields ...
        },
    )

    (
        optimized_content_instance,
        optimized_content_created,
    ) = await optimized_content_update(
        original_cover_letter=cover_letter_instance,
        defaults={
            "optimized_content": optimized_content,
            "analysis": analysis_instance,
        },
    )

    total = time.time() - start_time
    print("Total time taken: ", total)
    return optimized_content


def run_main():
    run_cover_letter_optimization(cover_letter, job_post_description)


{
    "success": "Optimization complete",
    "optimized_content": "Emily Johnson \n789 Healing Avenue \nToronto, ON, M4B 1Z6 \n(647) 555-0198 \nemily.johnson@fakemail.com \nOctober 30, 2023\n\nHiring Manager \nSt. Mary\u2019s Health Centre \n456 Wellness Road \nToronto, ON, L3T 7P9\n\nDear Hiring Manager,\n\nI am thrilled to apply for the Registered Nurse (RN) - Acute Care position at St. Mary\u2019s Health Centre. With my strong background in acute care nursing and a deep commitment to patient-focused care, I am eager to contribute to your team's esteemed reputation for empathetic service and clinical excellence. \n\nAs a dedicated RN with a Bachelor of Science in Nursing from the Toronto School of Health Sciences and over three years of experience in high-pressure acute care settings, I have honed a robust skill set that aligns with the demands of St. Mary's fast-paced environment. My current role at Good Health Hospital in Toronto has equipped me to excel in situations that require swift decision-making, precise assessments, and the execution of intricate treatment plans.\n\nKey achievements in my professional journey include:\n\n1. Effective management of patients with diverse and complex health conditions, ensuring compassionate and proficient treatment.\n2. Demonstrating a strong ability to work collaboratively with cross-functional health care teams to enhance patient care plans and outcomes.\n3. Advocacy for patient education, ensuring comprehensible discharge processes, which has notably decreased readmission rates.\n4. Maintaining diligent documentation practices, thereby enhancing the accuracy and reliability of patient records.\n\nThe holistic approach to health care at St. Mary\u2019s Health Centre and its emphasis on continuous professional development resonate with me. The prospect of working within an institution that offers a supportive work environment and values staff well-being is highly appealing to me.\n\nEnclosed is my resume for your review. I am eager to discuss how my clinical expertise and personal ethos can align with the noble mission of St. Mary\u2019s Health Centre. Please feel free to contact me at your earliest convenience by phone at (647) 555-0198 or via email at emily.johnson@fakemail.com.\n\nThank you for considering my application. I am confident in my ability to make a meaningful contribution to your distinguished team and am excited about the opportunity to bring my dedication and skills to your institution.\n\nWarm regards,\nEmily Johnson \nEnclosure: Resume\n",
}


"""
Emily Johnson 

789 Healing Avenue 
Toronto, ON, M4B 1Z6 
(647) 555-0198 
emily.johnson@fakemail.com 
October 30, 2023

Hiring Manager 
St. Mary's Health Centre 
456 Wellness Road 
Toronto, ON, L3T 7P9

Dear Hiring Manager,

I am thrilled to apply for the Registered Nurse (RN) - Acute Care position at St. Mary's Health Centre. With my strong background in acute care nursing and a deep commitment to patient-focused care, I am eager to contribute to your team's esteemed reputation for empathetic service and clinical excellence. 
As a dedicated RN with a Bachelor of Science in Nursing from the Toronto School of Health Sciences and over three years of experience in high-pressure acute care settings, I have honed a robust skill set that aligns with the demands of St. Mary's fast-paced environment. My current role at Good Health Hospital in Toronto has equipped me to excel in situations that require swift decision-making, precise assessments, and the execution of intricate treatment plans.

Key achievements in my professional journey include:
1. Effective management of patients with diverse and complex health conditions, ensuring compassionate and proficient treatment.
2. Demonstrating a strong ability to work collaboratively with cross-functional health care teams to enhance patient care plans and outcomes.
3. Advocacy for patient education, ensuring comprehensible discharge processes, which has notably decreased readmission rates.
4. Maintaining diligent documentation practices, thereby enhancing the accuracy and reliability of patient records.

The holistic approach to health care at St. Mary's Health Centre and its emphasis on continuous professional development resonate with me. The prospect of working within an institution that offers a supportive work environment and values staff well-being is highly appealing to me.

Enclosed is my resume for your review. I am eager to discuss how my clinical expertise and personal ethos can align with the noble mission of St. Mary's Health Centre. Please feel free to contact me at your earliest convenience by phone at (647) 555-0198 or via email at emily.johnson@fakemail.com.

Thank you for considering my application. I am confident in my ability to make a meaningful contribution to your distinguished team and am excited about the opportunity to bring my dedication and skills to your institution.

Warm regards,
Emily Johnson 
Enclosure: Resume
"""
