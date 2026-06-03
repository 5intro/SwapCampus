"""ASGI config for SwapCampus.

支持 HTTP 和 WebSocket（Django Channels）协议。
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 在导入 routing 前先初始化 Django ASGI application
django_asgi_app = get_asgi_application()

from config.routing import websocket_urlpatterns  # noqa: E402
from core.middleware import JWTAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
