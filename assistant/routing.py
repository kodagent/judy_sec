from django.urls import path

from assistant import consumers, optimizerconsumers

websocket_urlpatterns = [
    path("ws/chat/", consumers.ChatConsumer.as_asgi()),
    # Optimizers
    path("ws/optimize/", optimizerconsumers.OptimizationConsumer.as_asgi()),
]
