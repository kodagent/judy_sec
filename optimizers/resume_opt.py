import time

from asgiref.sync import sync_to_async

from chatbackend.configs.logging_config import configure_logger
from helpers.optimizer_utils import get_job_post_instruction
from optimizers.mg_database import get_doc_content
from optimizers.models import JobPost, OptimizedResumeContent, Resume
from optimizers.pdf_gen import generate_resume_pdf
from optimizers.samples import default_job_post, default_resume
from optimizers.utils import (
    Readablity,
    customize_doc,
    improve_doc,
    optimize_doc,
    resume_sections_feedback,
)

logger = configure_logger(__name__)


SYSTEM_ROLE = "system"
USER_ROLE = "user"


async def improve_resume(candidate_id):
    try:
        start_time = time.time()

        # get from the database, because the default is going to be created using some of the applicant details
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

        # Run the synchronous database update_or_create functions concurrently
        resume_instance, resume_created = await resume_update(
            resume_id=candidate_id,
            defaults={
                "general_improved_content": improved_content,
                "general_improved_pdf": pdf,
            },
        )
    except Exception as e:
        logger.error(e)

    total = time.time() - start_time
    logger.info(f"Total time taken: {total}")

    return resume_instance.general_improved_pdf.url


async def customize_improved_resume(candidate_id, custom_instruction):
    start_time = time.time()
    resume_update = sync_to_async(
        Resume.objects.update_or_create, thread_sensitive=True
    )

    resume_instance = await sync_to_async(Resume.objects.get)(resume_id=candidate_id)
    improved_content = resume_instance.general_improved_content
    customized_content = await customize_doc(
        doc_type="resume",
        doc_content=improved_content,
        custom_instruction=custom_instruction,
    )

    pdf = generate_resume_pdf(
        customized_content,
        filename="Customized Improved Resume.pdf",
    )

    # Run the synchronous database update_or_create functions concurrently
    resume_instance, resume_created = await resume_update(
        resume_id=candidate_id,
        defaults={
            "general_improved_content": customized_content,
            "general_improved_pdf": pdf,
        },
    )

    total = time.time() - start_time
    logger.info(f"Total time taken: {total}")

    return resume_instance.general_improved_pdf.url


async def customize_optimized_resume(applicant_id, job_post_id, custom_instruction):
    start_time = time.time()

    optimized_resume_update = sync_to_async(
        OptimizedResumeContent.objects.update_or_create, thread_sensitive=True
    )

    resume_instance = await sync_to_async(Resume.objects.get)(resume_id=applicant_id)
    optimized_resume_instance = await sync_to_async(OptimizedResumeContent.objects.get)(
        resume=resume_instance
    )
    job_post_instance = await sync_to_async(JobPost.objects.get)(
        job_post_id=job_post_id
    )

    optimized_content = optimized_resume_instance.optimized_content
    customized_content = await customize_doc(
        doc_type="resume",
        doc_content=optimized_content,
        custom_instruction=custom_instruction,
    )

    pdf = generate_resume_pdf(
        optimized_content, filename="Customized Optimized Resume.pdf"
    )

    # optimized_content_instance, created = await optimized_resume_update(
    #     resume=resume_instance,
    #     defaults={
    #         "optimized_content": optimized_content,
    #         "optimized_pdf": pdf,
    #         "is_tailored": True,
    #         "job_post": job_post_instance,
    #     },
    # )

    total = time.time() - start_time
    logger.info(f"Total time taken: {total}")
    return "optimized_content_instance.optimized_pdf.url"


async def optimize_resume(applicant_id, job_post_id):
    start_time = time.time()

    optimized_resume_update = sync_to_async(
        OptimizedResumeContent.objects.update_or_create, thread_sensitive=True
    )

    resume_instance = await sync_to_async(Resume.objects.get)(resume_id=applicant_id)
    job_post_instance = await sync_to_async(JobPost.objects.get)(
        job_post_id=job_post_id
    )

    optimized_content = await optimize_doc(
        doc_type="resume",
        doc_text=resume_instance.general_improved_content,
        job_description=job_post_instance.optimized_content,
    )

    pdf = generate_resume_pdf(optimized_content, filename="Optimized Resume.pdf")

    optimized_content_instance, created = await optimized_resume_update(
        resume=resume_instance,
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
