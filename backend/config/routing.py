"""WebSocket 路由配置（Django Channels）."""

from django.urls import path

from apps.chat.consumers import ChatConsumer

websocket_urlpatterns = [
    # 聊天 WebSocket：ws://host/ws/chat/<conversation_uuid>/
    path("ws/chat/<str:conversation_uuid>/", ChatConsumer.as_asgi()),
]
