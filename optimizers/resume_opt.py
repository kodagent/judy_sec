import time

import textstat
from asgiref.sync import sync_to_async

from chatbackend.configs.base_config import openai_client as client
from chatbackend.configs.logging_config import configure_logger
from helpers.optimizer_utils import get_job_post_instruction, job_post_description
from optimizers.mg_database import get_doc_content
from optimizers.models import JobPost, OptimizedJobPostContent, Resume
from optimizers.pdf_gen import generate_resume_pdf
from optimizers.utils import (
    Readablity,
    default_resume,
    get_chat_response,
    improve_doc,
    resume_sections_feedback,
)

logger = configure_logger(__name__)


SYSTEM_ROLE = "system"
USER_ROLE = "user"


async def improve_resume(candidate_id):
    try:
        start_time = time.time()

        # resume_content = await get_doc_content(candidate_id, doc_type="R")
        resume_content = default_resume

        resume_update = sync_to_async(
            Resume.objects.update_or_create, thread_sensitive=True
        )

        readability = Readablity(resume_content)
        readability_feedback = await readability.get_readability_text(doc_type="resume")

        sections_feedback = await resume_sections_feedback(resume_content)

        feedbacks = [readability_feedback, sections_feedback]

        resume_feedback = "\n\n".join(feedbacks)

        improved_content = await improve_doc(
            doc_type="resume",
            doc_content=resume_content,
            doc_feedback=resume_feedback,
        )

        pdf = generate_resume_pdf(improved_content, filename="Improved Resume.pdf")

        # # Run the synchronous database update_or_create functions concurrently
        # resume_instance, resume_created = await resume_update(
        #     resume_id=candidate_id,
        #     defaults={
        #         "general_improved_content": improved_content,
        #         "general_improved_pdf": pdf,
        #     },
        # )
    except Exception as e:
        logger.error(e)

    total = time.time() - start_time
    logger.info(f"Total time taken: {total}")

    return "resume_instance.general_improved_pdf.url"


async def optimize_resume(applicant_id, job_post_id):
    start_time = time.time()

    job_post_update = sync_to_async(
        JobPost.objects.update_or_create, thread_sensitive=True
    )
    optimized_job_post_update = sync_to_async(
        OptimizedJobPostContent.objects.update_or_create, thread_sensitive=True
    )


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

    optimized_content = get_chat_response(instruction, content)
    return optimized_content


# ------------------------ OTHER DOCS ------------------------
async def job_post(
    owner_id, document_id
):  # might not need the owner id for this afterall
    job_post_content = await get_doc_content(owner_id, doc_type="JP")

    instruction = get_job_post_instruction(job_role="Backend Engineer")
    response = get_openai_response(instruction, job_post_content)
    print(response)
    return response
