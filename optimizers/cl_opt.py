import asyncio
import time

from asgiref.sync import sync_to_async
from celery import shared_task
from django.conf import settings

from chatbackend.configs.logging_config import configure_logger
from helpers.optimizer_utils import cover_letter
from optimizers.mg_database import get_doc_content
from optimizers.models import (
    CoverLetter,
    CoverLetterAnalysis,
    JobPost,
    OptimizedCoverLetterContent,
)
from optimizers.pdf_gen import generate_formatted_pdf
from optimizers.samples import default_cover_letter
from optimizers.utils import (
    Polarity,
    Readablity,
    check_grammar_and_spelling,
    improve_doc,
    optimize_doc,
    review_tone,
)

logger = configure_logger(__name__)

SYSTEM_ROLE = "system"
USER_ROLE = "user"


@shared_task
async def get_default_cover_letter(candidate_id):
    try:
        resume_content = await get_doc_content(candidate_id, doc_type="R")

        cover_letter_update = sync_to_async(
            CoverLetter.objects.update_or_create, thread_sensitive=True
        )

        created_cl = create_doc(
            "cover letter", "resume", resume_content, default_cover_letter
        )

        pdf = generate_formatted_pdf(
            created_cl, filename="Base Cover Letter.pdf", doc_type="CL"
        )

        # Run the synchronous database update_or_create functions concurrently
        cover_letter_instance, cover_letter_created = await cover_letter_update(
            cover_letter_id=candidate_id,
            defaults={
                "original_content": created_cl,
                "original_pdf": pdf,
            },
        )

    except Exception as e:
        logger.error(e)

    total = time.time() - start_time
    logger.info("Total time taken: ", total)

    return cover_letter_instance.original_pdf.url


@shared_task
async def improve_cover_letter(candidate_id):
    try:
        start_time = time.time()

        # get from the database, because the default is going to be created using some of the applicant details
        # cover_letter_content = await get_doc_content(candidate_id, doc_type="CL")
        cover_letter_content = default_cover_letter

        cover_letter_update = sync_to_async(
            CoverLetter.objects.update_or_create, thread_sensitive=True
        )

        readability = Readablity(cover_letter_content)
        readability_feedback = await readability.get_readability_text(
            doc_type="cover letter"
        )

        polarity = Polarity(cover_letter_content)
        polarity_feedback = await polarity.get_polarity_text(doc_type="cover letter")

        # corrections = await check_grammar_and_spelling(cover_letter_content),
        tone_feedback = await review_tone(
            doc_type="cover letter", text=cover_letter_content
        )

        feedbacks = [
            readability_feedback,
            polarity_feedback,
            tone_feedback,
        ]

        cover_letter_feedback = "\n\n".join(feedbacks)

        improved_content = await improve_doc(
            doc_type="cover letter",
            doc_content=cover_letter_content,
            doc_feedback=cover_letter_feedback,
        )

        pdf = generate_formatted_pdf(
            improved_content, filename="Improved Cover Letter.pdf", doc_type="CL"
        )

        # Run the synchronous database update_or_create functions concurrently
        cover_letter_instance, cover_letter_created = await cover_letter_update(
            cover_letter_id=candidate_id,
            defaults={
                "general_improved_content": improved_content,
                "general_improved_pdf": pdf,
            },
        )
    except Exception as e:
        logger.error(e)

    total = time.time() - start_time
    logger.info("Total time taken: ", total)

    return cover_letter_instance.general_improved_pdf.url


@shared_task
async def optimize_cover_letter(applicant_id, job_post_id):
    start_time = time.time()

    optimized_cover_letter_update = sync_to_async(
        OptimizedCoverLetterContent.objects.update_or_create, thread_sensitive=True
    )
    cover_letter_instance = await sync_to_async(CoverLetter.objects.get)(
        cover_letter_id=applicant_id
    )

    job_post_instance = await sync_to_async(JobPost.objects.get)(
        job_post_id=job_post_id
    )

    optimized_content = await optimize_doc(
        doc_type="cover letter",
        doc_text=cover_letter_instance.general_improved_content,
        job_description=job_post_instance.optimized_content,
    )

    pdf = generate_formatted_pdf(
        optimized_content, filename="Optimized Cover Letter.pdf", doc_type="CL"
    )

    optimized_content_instance, created = await optimized_cover_letter_update(
        cover_letter=cover_letter_instance,
        defaults={
            "optimized_content": optimized_content,
            "optimized_pdf": pdf,
            "is_tailored": True,
            "job_post": job_post_instance,
        },
    )

    total = time.time() - start_time
    logger.info(f"Total time taken: {total}")
    return optimized_content_instance.optimized_pdf.url


@shared_task
async def customize_improved_cover_letter(candidate_id, custom_instruction):
    start_time = time.time()

    cover_letter_update = sync_to_async(
        CoverLetter.objects.update_or_create, thread_sensitive=True
    )

    cover_letter_instance = await sync_to_async(CoverLetter.objects.get)(
        cover_letter_id=candidate_id
    )
    improved_content = cover_letter_instance.general_improved_content
    customized_content = await customize_doc(
        doc_type="cover letter",
        doc_content=improved_content,
        custom_instruction=custom_instruction,
    )

    pdf = generate_resume_pdf(
        customized_content, filename="Customized Improved Cover Letter.pdf"
    )

    # Run the synchronous database update_or_create functions concurrently
    cover_letter_instance, cover_letter_created = await cover_letter_update(
        cover_letter_id=candidate_id,
        defaults={
            "general_improved_content": customized_content,
            "general_improved_pdf": pdf,
        },
    )

    total = time.time() - start_time
    logger.info(f"Total time taken: {total}")

    return cover_letter_instance.general_improved_pdf.url


@shared_task
async def customize_optimized_cover_letter(
    applicant_id, job_post_id, custom_instruction
):
    start_time = time.time()

    optimized_cover_letter_update = sync_to_async(
        OptimizedCoverLetterContent.objects.update_or_create, thread_sensitive=True
    )

    cover_letter_instance = await sync_to_async(CoverLetter.objects.get)(
        cover_letter_id=applicant_id
    )
    optimized_cover_letter_instance = await sync_to_async(
        OptimizedCoverLetterContent.objects.get
    )(cover_letter=cover_letter_instance)
    job_post_instance = await sync_to_async(JobPost.objects.get)(
        job_post_id=job_post_id
    )

    optimized_content = optimized_cover_letter_instance.optimized_content
    customized_content = await customize_doc(
        doc_type="cover letter",
        doc_content=optimized_content,
        custom_instruction=custom_instruction,
    )

    pdf = generate_formatted_pdf(
        customized_content,
        filename="Customized Optimized Cover Letter.pdf",
        doc_type="CL",
    )

    optimized_content_instance, created = await optimized_cover_letter_update(
        cover_letter=cover_letter_instance,
        defaults={
            "optimized_content": optimized_content,
            "optimized_pdf": pdf,
            "is_tailored": True,
            "job_post": job_post_instance,
        },
    )

    total = time.time() - start_time
    logger.info(f"Total time taken: {total}")
    return optimized_content_instance.optimized_pdf.url


{
    "success": "Optimization complete",
    "optimized_content": "Emily Johnson \n789 Healing Avenue \nToronto, ON, M4B 1Z6 \n(647) 555-0198 \nemily.johnson@fakemail.com \nOctober 30, 2023\n\nHiring Manager \nSt. Mary\u2019s Health Centre \n456 Wellness Road \nToronto, ON, L3T 7P9\n\nDear Hiring Manager,\n\nI am thrilled to apply for the Registered Nurse (RN) - Acute Care position at St. Mary\u2019s Health Centre. With my strong background in acute care nursing and a deep commitment to patient-focused care, I am eager to contribute to your team's esteemed reputation for empathetic service and clinical excellence. \n\nAs a dedicated RN with a Bachelor of Science in Nursing from the Toronto School of Health Sciences and over three years of experience in high-pressure acute care settings, I have honed a robust skill set that aligns with the demands of St. Mary's fast-paced environment. My current role at Good Health Hospital in Toronto has equipped me to excel in situations that require swift decision-making, precise assessments, and the execution of intricate treatment plans.\n\nKey achievements in my professional journey include:\n\n1. Effective management of patients with diverse and complex health conditions, ensuring compassionate and proficient treatment.\n2. Demonstrating a strong ability to work collaboratively with cross-functional health care teams to enhance patient care plans and outcomes.\n3. Advocacy for patient education, ensuring comprehensible discharge processes, which has notably decreased readmission rates.\n4. Maintaining diligent documentation practices, thereby enhancing the accuracy and reliability of patient records.\n\nThe holistic approach to health care at St. Mary\u2019s Health Centre and its emphasis on continuous professional development resonate with me. The prospect of working within an institution that offers a supportive work environment and values staff well-being is highly appealing to me.\n\nEnclosed is my resume for your review. I am eager to discuss how my clinical expertise and personal ethos can align with the noble mission of St. Mary\u2019s Health Centre. Please feel free to contact me at your earliest convenience by phone at (647) 555-0198 or via email at emily.johnson@fakemail.com.\n\nThank you for considering my application. I am confident in my ability to make a meaningful contribution to your distinguished team and am excited about the opportunity to bring my dedication and skills to your institution.\n\nWarm regards,\nEmily Johnson \nEnclosure: Resume\n",
}

{
    "sender_info": {
        "name": "Emily Johnson",
        "address": "789 Healing Avenue, Toronto, ON, M4B 1Z6",
        "phone": "(647) 555-0198",
        "email": "emily.johnson@fakemail.com",
        "date": "October 30, 2023",
    },
    "recipient_info": {
        "name": "Hiring Manager",
        "address": "St. Mary's Health Centre, 456 Wellness Road, Toronto, ON, L3T 7P9",
    },
    "body": "Dear Hiring Manager,\n\nI am thrilled to apply for the Registered Nurse (RN) - Acute Care position at St. Mary's Health Centre. With my strong background in acute care nursing and commitment to patient-focused care, I am ready to contribute to your team's reputation for empathetic service and clinical excellence. \nAs a dedicated RN with a Bachelor of Science in Nursing and over three years of experience in high-pressure acute care, I possess a robust skill set ideal for St. Mary's fast-paced environment. My role at Good Health Hospital in Toronto has prepared me for quick decision-making, precise assessments, and implementing complex treatment plans.\n\nSome key achievements include:\n- Managing patients with diverse and complex health conditions, providing compassionate and proficient care.\n- Collaborating with cross-functional health care teams to improve patient care plans and outcomes.\n- Advocating for patient education to ensure clear discharge processes, contributing to reduced readmission rates.\n- Enhancing patient record accuracy and reliability through diligent documentation.\n\nSt. Mary's Health Centre's holistic approach and commitment to professional development strongly resonate with me. The prospect of working in a supportive environment that values staff well-being is highly appealing.\n\nPlease find my resume enclosed for your review. I look forward to discussing how my clinical expertise and personal values align with St. Mary's mission. You can reach me at (647) 555-0198 or emily.johnson@fakemail.com.\n\nThank you for considering my application. I am eager to bring my dedication and skills to your esteemed team.\n\nWarm regards,\nEmily Johnson\nEnclosure: Resume",
}

# https://judy-dev.essentialrecruit-api.com/api/optimizers/optimize-cover-letter/63a6af57677ed8a015025a62/65aa68567bd03fff776fbfcf/
