import json

from channels.generic.websocket import AsyncWebsocketConsumer

from chatbackend.configs.logging_config import configure_logger
from optimizers.cl_opt import cl_optimize_func, customize_opt_cl
from optimizers.resume_opt import (customize_resume_optimize_func,
                                   resume_optimize_func)

logger = configure_logger(__name__)

class OptimizationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Retrieve the applicant_id from the query string
        self.applicant_id = self.scope["query_string"].decode("utf-8").split("=")[1]
        self.group_name_resume = f"user_{self.applicant_id}_resume"
        self.group_name_cl = f"user_{self.applicant_id}_cl"

        # Add to both groups
        await self.channel_layer.group_add(self.group_name_resume, self.channel_name)
        await self.channel_layer.group_add(self.group_name_cl, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        logger.info("...Disconnected")

        # Remove this channel from both groups
        await self.channel_layer.group_discard(self.group_name_resume, self.channel_name)
        await self.channel_layer.group_discard(self.group_name_cl, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        process_type = text_data_json.get("process_type")
        applicant_id = text_data_json.get("applicant_id")
        job_post_id = text_data_json.get("job_post_id")
        custom_instruction = text_data_json.get("custom_instruction")

        if process_type == "resume_optimization":
            return_data = await resume_optimize_func(applicant_id, job_post_id)
            group_name = self.group_name_resume

        elif process_type == "customize_optimized_resume":
            return_data = await customize_resume_optimize_func(applicant_id, job_post_id, custom_instruction)
            group_name = self.group_name_resume

        elif process_type == "cover_letter_optimization":
            return_data = await cl_optimize_func(applicant_id, job_post_id)
            group_name = self.group_name_cl

        elif process_type == "customize_optimized_cover_letter":
            return_data = await customize_opt_cl(applicant_id, job_post_id, custom_instruction)
            group_name = self.group_name_cl

        # Send data back through the WebSocket
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "optimization.message",
                "message": json.dumps({"url": return_data})
            }
        )

    # Handler for sending messages to the WebSocket, added for group_send
    async def optimization_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=message)
