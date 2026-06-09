"""站内通讯模型.

- Conversation：会话（多对多聊天，支持商品咨询上下文）
- Message：消息（文本内容，已读状态追踪）
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel


class Conversation(BaseModel):
    """会话模型.

    每个会话关联多个参与者和一个可选商品（用于商品咨询上下文）。
    """

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversations",
        verbose_name="参与者",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
        verbose_name="关联商品",
        help_text="通过商品页面发起的咨询会关联该商品",
    )
    # 会话的标题/名称，用于列表展示
    title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="会话标题",
        help_text="如未设置则使用参与者昵称拼接",
    )

    class Meta:
        db_table = "conversations"
        verbose_name = "会话"
        verbose_name_plural = verbose_name
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title or f"会话 {self.id}"

    def get_title_for_user(self, user) -> str:
        """获取会话在指定用户视角下的显示名称."""
        if self.title:
            return self.title
        others = self.participants.exclude(id=user.id)
        if others.exists():
            return ", ".join(other.get_display_name() for other in others[:3])
        return f"会话 {self.id.hex[:8]}"

    @property
    def last_message(self) -> "Message | None":
        """获取最后一条消息（用于列表预览）."""
        return self.messages.order_by("-created_at").first()


class Message(BaseModel):
    """消息模型.

    每条消息属于一个会话，记录发送者和文本内容。
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="所属会话",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name="发送者",
    )
    content = models.TextField(
        max_length=2000,
        verbose_name="消息内容",
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="已读状态",
    )
    is_recalled = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="已撤回",
        help_text="消息是否已被发送者撤回",
    )
    recalled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="撤回时间",
    )

    class Meta:
        db_table = "messages"
        verbose_name = "消息"
        verbose_name_plural = verbose_name
        ordering = ["created_at"]  # 消息按时间正序排列
        indexes = [
            models.Index(fields=["conversation", "-created_at"]),
            models.Index(fields=["sender", "is_read"]),
        ]

    def __str__(self) -> str:
        return f"{self.sender.get_display_name()}: {self.content[:50]}"
