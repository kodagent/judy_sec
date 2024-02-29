import json

from channels.generic.websocket import AsyncWebsocketConsumer

from optimizers.cl_opt import customize_optimized_cover_letter, optimize_cover_letter
from optimizers.resume_opt import customize_optimized_resume, optimize_resume


class OptimizationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # self.applicant_id = self.scope["url_route"]["kwargs"]["applicant_id"]
        # self.job_post_id = self.scope["url_route"]["kwargs"]["job_post_id"]

        await self.accept()

    async def disconnect(self, close_code):
        # Handle disconnection
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        process_type = text_data_json.get("process_type")
        applicant_id = text_data_json.get("applicant_id")
        job_post_id = text_data_json.get("job_post_id")
        custom_instruction = text_data_json.get("custom_instruction")

        if process_type == "resume_optimization":
            return_data = optimize_resume(applicant_id, job_post_id)

        if process_type == "customize_optimized_resume":
            return_data = customize_optimized_resume(
                applicant_id, job_post_id, custom_instruction
            )

        if process_type == "cover_letter_optimization":
            return_data = optimize_cover_letter(applicant_id, job_post_id)

        if process_type == "customize_optimized_cover_letter":
            return_data = customize_optimized_cover_letter(
                applicant_id, job_post_id, custom_instruction
            )

        # Send data back through the WebSocket
        await self.send(text_data=json.dumps({"url": return_data}))
