"""WebSocket 消费者：实时聊天.

支持的操作：
- 连接/断开
- 发送消息 → 广播给会话所有参与者
- 标记已读 → 通知发送者消息已读

前端连接方式：
new WebSocket("ws://host/ws/chat/<conversation_uuid>/?token=<jwt_access_token>")
"""

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """聊天 WebSocket Consumer.

    每个用户连接到一个 conversation room，
    使用 Channels group 广播消息给所有在线参与者。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_uuid = None
        self.group_name = None
        self.user = None

    async def connect(self):
        """建立 WebSocket 连接.

        1. 从 scope 获取已验证的用户（由 JWTAuthMiddleware 注入）
        2. 验证用户是否为会话参与者
        3. 加入 Channels group
        """
        self.user = self.scope.get("user")

        # 未认证用户拒绝连接
        if not self.user or not self.user.is_authenticated:
            logger.warning("WebSocket connection rejected: unauthenticated user")
            await self.close(code=4001)
            return

        # 获取会话 UUID
        self.conversation_uuid = self.scope["url_route"]["kwargs"]["conversation_uuid"]

        # 验证用户是否为会话参与者
        is_participant = await self._is_participant(self.conversation_uuid, self.user)
        if not is_participant:
            logger.warning(
                f"WebSocket connection rejected: user {self.user.username} "
                f"not in conversation {self.conversation_uuid}"
            )
            await self.close(code=4003)
            return

        # 加入会话组
        self.group_name = f"chat_{self.conversation_uuid}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()
        logger.info(
            f"WebSocket connected: user={self.user.username}, "
            f"conversation={self.conversation_uuid}"
        )

        # 通知其他参与者用户已上线（可选）
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "user_status",
                "user_id": str(self.user.id),
                "username": self.user.username,
                "status": "online",
            },
        )

    async def disconnect(self, close_code):
        """断开连接，离开 group."""
        if self.group_name:
            # 通知离线
            if self.user and self.user.is_authenticated:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "user_status",
                        "user_id": str(self.user.id),
                        "username": self.user.username,
                        "status": "offline",
                    },
                )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(
            f"WebSocket disconnected: user={getattr(self.user, 'username', '?')}, "
            f"code={close_code}"
        )

    # ── 消息接收 ──────────────────────────────────────────

    async def receive_json(self, content, **kwargs):
        """处理客户端发来的 JSON 消息.

        支持的消息类型：
        - chat_message: 发送聊天消息
        - mark_read: 标记消息已读
        """
        msg_type = content.get("type")

        if msg_type == "chat_message":
            await self._handle_chat_message(content)
        elif msg_type == "mark_read":
            await self._handle_mark_read(content)
        elif msg_type == "read_conversation":
            await self._handle_read_conversation(content)
        elif msg_type == "typing":
            await self._handle_typing(content)
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def _handle_chat_message(self, content):
        """处理聊天消息：保存到数据库并广播."""
        text = content.get("content", "").strip()
        if not text:
            return
        if len(text) > 2000:
            await self.send_json(
                {"type": "error", "error": "消息长度不能超过 2000 字"}
            )
            return

        # 保存消息到数据库
        message = await self._save_message(text)

        # 广播给会话组内所有在线用户（包括自己，用于多端同步）
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": str(message["id"]),
                    "conversation": self.conversation_uuid,
                    "sender_id": str(self.user.id),
                    "sender_name": self.user.get_display_name(),
                    "content": text,
                    "is_read": False,
                    "created_at": message["created_at"].isoformat(),
                },
            },
        )

    async def _handle_mark_read(self, content):
        """处理已读标记：更新数据库并通知发送者."""
        message_ids = content.get("message_ids", [])
        if not message_ids:
            return

        # 批量更新数据库中消息的已读状态
        updated_count = await self._mark_messages_read(message_ids)

        if updated_count > 0:
            # 广播已读事件
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "messages_read",
                    "reader_id": str(self.user.id),
                    "message_ids": message_ids,
                },
            )

    async def _handle_read_conversation(self, content):
        """处理已读会话：将该会话中对方发的所有未读消息标记为已读."""
        # 批量标记对方发的未读消息为已读
        message_ids = await self._mark_conversation_read()

        if message_ids:
            # 广播已读事件
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "messages_read",
                    "reader_id": str(self.user.id),
                    "message_ids": message_ids,
                },
            )

    async def _handle_typing(self, content):
        """处理输入状态提醒."""
        is_typing = content.get("is_typing", False)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_status",
                "user_id": str(self.user.id),
                "username": self.user.get_display_name(),
                "is_typing": is_typing,
            },
        )

    # ── 事件处理器（由 group_send 触发）───────────────────

    async def chat_message(self, event):
        """将新消息推送给 WebSocket 客户端."""
        await self.send_json(
            {
                "type": "new_message",
                "message": event["message"],
            }
        )

    async def messages_read(self, event):
        """通知消息已读."""
        await self.send_json(
            {
                "type": "messages_read",
                "reader_id": event["reader_id"],
                "message_ids": event["message_ids"],
            }
        )

    async def user_status(self, event):
        """通知用户在线状态变化."""
        await self.send_json(
            {
                "type": "user_status",
                "user_id": event["user_id"],
                "username": event["username"],
                "status": event["status"],
            }
        )

    async def typing_status(self, event):
        """通知输入状态."""
        await self.send_json(
            {
                "type": "typing",
                "user_id": event["user_id"],
                "username": event["username"],
                "is_typing": event["is_typing"],
            }
        )

    # ── 数据库操作（异步化）────────────────────────────────

    @database_sync_to_async
    def _is_participant(self, conversation_uuid: str, user) -> bool:
        """检查用户是否为会话参与者."""
        from apps.chat.models import Conversation

        return Conversation.objects.filter(
            id=conversation_uuid, participants=user
        ).exists()

    @database_sync_to_async
    def _save_message(self, text: str) -> dict:
        """保存消息到数据库并更新会话时间."""
        from apps.chat.models import Conversation, Message

        conversation = Conversation.objects.get(id=self.conversation_uuid)
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=text,
        )
        # 刷新会话的 updated_at
        conversation.save(update_fields=["updated_at"])

        return {
            "id": str(msg.id),
            "created_at": msg.created_at,
        }

    @database_sync_to_async
    def _mark_messages_read(self, message_ids: list[str]) -> int:
        """批量标记消息为已读（仅标记非自己发送的消息）."""
        from apps.chat.models import Message

        return Message.objects.filter(
            id__in=message_ids,
            is_read=False,
        ).exclude(sender=self.user).update(is_read=True)

    @database_sync_to_async
    def _mark_conversation_read(self) -> list[str]:
        """将该会话中对方发的所有未读消息标记为已读，返回已更新的消息ID列表."""
        from apps.chat.models import Message

        qs = Message.objects.filter(
            conversation_id=self.conversation_uuid,
            is_read=False,
        ).exclude(sender=self.user)

        # 先获取 ID 列表再更新
        message_ids = list(qs.values_list("id", flat=True))
        if message_ids:
            qs.update(is_read=True)
        return [str(mid) for mid in message_ids]
