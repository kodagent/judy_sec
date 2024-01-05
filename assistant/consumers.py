import json
import time
import uuid
from datetime import datetime

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from openai import OpenAI

from assistant.knowledge import query_vec_database
from assistant.memory import BaseMemory
from assistant.models import Conversation
from assistant.tasks import save_conversation
from chatbackend.logging_config import configure_logger

logger = configure_logger(__name__)


client = OpenAI(api_key=settings.OPENAI_API_KEY)


class ChatConsumer(AsyncWebsocketConsumer):
    """
        ChatConsumer handles WebSocket connections for chat rooms, managing user messages,
        chatbot responses, and conversation state.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def connect(self):
        """
            Handles a new WebSocket connection, joining the user to the appropriate chat room,
            and initializing the conversation state.
        """
        logger.info("---------- CONNECTION ATTEMPT RECEIVED ----------")
        
        # Generate a unique ID for the conversation
        self.room_name = str(uuid.uuid4())
        self.room_group_name = f'chat_{self.room_name}'

        self.conversation_memory = BaseMemory()

        # Create the Conversation instance without setting the customer and channel
        self.conversation = await database_sync_to_async(Conversation.objects.create)()

        # Initialize the conversation start time
        self.conversation_memory.session_start_time = datetime.now()
        logger.info(f"Conversation start time: {self.conversation_memory.session_start_time}")

        # Send message to room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        logger.info("---------- CONNECTION DISCONNECTED ----------")
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        logger.info("---------- MESSAGE RECEIVED ----------")

        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        try:
            logger.info(f"MESSAGE TYPE: {message_type}")

            if message_type == 'user_message':
                start = time.time()
                self.user_id = text_data_json.get('userId')
                user_message = text_data_json.get('message')
                message_id = str(uuid.uuid4())

                context1, context2 = await query_vec_database(query=user_message, num_results=2, pinecone_index_name=settings.PINECONE_INDEX_NAME)
                context = context1['metadata']['text'] + "\n\n" + context2['metadata']['text']

                # if we want to store this data in the database (connect it to message id)
                # context_text_1, context_score_1 = context1['metadata']['text'], context1['score']
                # context_text_2, context_score_2 = context2['metadata']['text'], context2['score']
                # context_text_3, context_score_3 = context3['metadata']['text'], context3['score']

                # build our prompt with the retrieved contexts included
                prompt_start = ("Answer the question based on the context below.\n\n" + "Context:\n")
                prompt_end = (f"\n\nQuestion: {user_message}\nAnswer:")
                user_ques = (prompt_start + "\n\n---\n\n" + context + prompt_end)
                
                self.conversation_memory.add_message(role='user', content=user_ques, message_id=message_id)

                bot_response = await self.generate_bot_response(user_ques)
                # logger.info(bot_response)

                stop = time.time()
                duration = stop - start
                
                # Add to the conversation tracker
                judy_response_id = str(uuid.uuid4())
                self.conversation_memory.add_message(role='assistant', content=bot_response, duration=duration, message_id=judy_response_id)
                
                logger.info(f"RESPONSE DURATION: {duration}")

                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': bot_response, 
                        'messageId': message_id
                    }
                )

            elif message_type == 'upvote':
                message_id = text_data_json.get('messageId')
                self.conversation_memory.upvote(message_id)
                logger.info(f"MESSAGE {message_id} UPVOTED!")

            elif message_type == 'downvote':
                message_id = text_data_json.get('messageId')
                self.conversation_memory.downvote(message_id)
                logger.info(f"MESSAGE {message_id} DOWNVOTED!")
            
            elif message_type == 'end_session':
                self.username_id = text_data_json.get('userId')
                self.email = text_data_json.get('email')
                self.name = text_data_json.get('name')
                self.role = text_data_json.get('role')
                self.user_detail = [self.username_id, self.email, self.name, self.role]
                await self.end_conversation()

                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': "session_ended", 
                    }
                )

        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
            return
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing the received data: {str(e)}")
            return

    # Receive message from room group
    async def chat_message(self, event):
        """
        Receives a message from the room group and sends it to the WebSocket.
        """
        logger.info("---------- FORWARDING BOT MESSAGE ----------")

        message = event.get('message')  
        message_id = event.get('messageId')    

        json_message = json.dumps({
            'message': message,
            'messageId': message_id
        })    

        logger.info(f"MESSAGE TO WEBSOCKET: ")
        logger.info(f"{json_message}")

        # Send message to WebSocket
        await self.send(text_data=json_message)

    # ----------------------- CUSTOM ASYNC FUNCTIONS --------------------------
    async def generate_bot_response(self, user_message):
        logger.info("---------- BOT ENGINE STARTED ----------")

        full_history = self.conversation_memory.get_openai_history()

        logger.info(f"CONVERSATION MEMORY: ")
        logger.info(full_history)

        # Make a copy and remove the most recent message (presumably the user's latest question)
        history_except_last = full_history[:-1]  # RECTIFY: this should be the latest context not latest question
        
        messages = [
            {
                "role": "system",
                "content": "You are a polite, friendly, helpful assistant that answers questions from the context given"
            },
            *full_history
        ]

        final_response = self.single_bot_query(messages)
                    
        logger.info("---------- BOT ENGINE STOPPED ----------")
        return final_response
    
    async def end_conversation(self):
        # self.conversation = await database_sync_to_async(Conversation.objects.create)()
        self.conversation_memory.session_end_time = datetime.now()
        conversation_memory_dict = self.conversation_memory.to_dict()
        save_conversation.apply_async(args=[conversation_memory_dict, str(self.thread_id), self.user_detail, "learn"])
        
        return "Done!"

    async def single_bot_query(self, messages):
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages
        )
        return response["choices"][0]["message"]["content"]
    # ----------------------- CUSTOM ASYNC FUNCTIONS --------------------------
 