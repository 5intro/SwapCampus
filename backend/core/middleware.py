"""Channels WebSocket JWT 鉴权中间件.

WebSocket 连接建立时从 query string 提取 JWT token，
验证后将 user 注入 scope，Consumer 可直接访问 scope["user"]。
"""

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token: str):
    """异步验证 JWT token 并返回 user 对象."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        validated_token = AccessToken(token)
        user = User.objects.get(id=validated_token["user_id"])
        return user
    except (InvalidToken, TokenError, KeyError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware:
    """Channels 中间件：从 WebSocket query string 解析 JWT，注入 scope["user"].

    前端连接方式：
    new WebSocket("ws://host/ws/chat/<uuid>/?token=<access_token>")
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = None
        # 解析 query string 中的 token 参数
        for param in query_string.split("&"):
            if param.startswith("token="):
                token = param.split("=", 1)[1]
                break

        scope["user"] = (
            await get_user_from_token(token) if token else AnonymousUser()
        )
        return await self.inner(scope, receive, send)
