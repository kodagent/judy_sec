import time

from asgiref.sync import sync_to_async

from chatbackend.configs.logging_config import configure_logger
from optimizers.mg_database import get_job_post_content
from optimizers.models import JobPost
from optimizers.utils import get_job_post_feedback, improve_doc

# Logging setup
logger = configure_logger(__name__)

SYSTEM_ROLE = "system"
USER_ROLE = "user"


async def optimize_job_post(job_post_id):
    start_time = time.time()

    job_post_update = sync_to_async(
        JobPost.objects.update_or_create, thread_sensitive=True
    )

    job_post_content = await get_job_post_content(job_post_id)

    job_post_feeback = await get_job_post_feedback(job_post_content)

    optimized_content = await improve_doc(
        "job post", job_post_content, job_post_feeback
    )

    job_post_instance, job_post_created = await job_post_update(
        job_post_id=job_post_id,
        defaults={
            "original_content": job_post_content,
            "optimized_content": optimized_content,
        },
    )

    total = time.time() - start_time
    logger.info(f"Total time taken: {total}")

    return job_post_instance.optimized_content
