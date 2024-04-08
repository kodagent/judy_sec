import json

from channels.generic.websocket import AsyncWebsocketConsumer

from chatbackend.configs.logging_config import configure_logger
from optimizers.cl_opt import cl_optimize_func, customize_opt_cl
from optimizers.resume_opt import customize_resume_optimize_func, resume_optimize_func
from assistant.tasks import create_conversation

logger = configure_logger(__name__)


class OptimizationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Retrieve the applicant_id from the query string
        self.applicant_id = self.scope["query_string"].decode("utf-8").split("=")[1]
        self.group_name = f"user_{self.applicant_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        logger.info("...Disconnected")

        # Remove this channel from the group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        process_type = text_data_json.get("process_type")
        applicant_id = text_data_json.get("applicant_id")
        job_post_id = text_data_json.get("job_post_id")
        custom_instruction = text_data_json.get("custom_instruction")

        if process_type == "resume_optimization":
            return_data = await resume_optimize_func(applicant_id, job_post_id)

        if process_type == "customize_optimized_resume":
            return_data = await customize_resume_optimize_func(
                applicant_id, job_post_id, custom_instruction
            )

        if process_type == "cover_letter_optimization":
            return_data = await cl_optimize_func(applicant_id, job_post_id)

        if process_type == "customize_optimized_cover_letter":
            return_data = await customize_opt_cl(
                applicant_id, job_post_id, custom_instruction
            )

        # Send data back through the WebSocket
        await self.send(text_data=json.dumps({"url": return_data}))
