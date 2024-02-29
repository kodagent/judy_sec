from django.urls import path
from optimizerconsumers import OptimizationConsumer

from assistant import consumers

websocket_urlpatterns = [
    path("ws/chat/", consumers.ChatConsumer.as_asgi()),
    # Optimizers
    path("ws/optimize/", OptimizationConsumer.as_asgi()),
]
