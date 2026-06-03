"""站内通讯序列化器."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.chat.models import Conversation, Message

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# 消息
# ═══════════════════════════════════════════════════════════
class MessageSerializer(serializers.ModelSerializer):
    """消息序列化器."""

    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "content",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "is_read",
            "created_at",
        ]

    def get_sender_name(self, obj) -> str:
        return obj.sender.get_display_name()


# ═══════════════════════════════════════════════════════════
# 会话
# ═══════════════════════════════════════════════════════════
class ConversationListSerializer(serializers.ModelSerializer):
    """会话列表序列化器（含最后一条消息预览和未读计数）."""

    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participant_names = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "participant_names",
            "product",
            "last_message",
            "unread_count",
            "created_at",
            "updated_at",
        ]

    def get_title(self, obj) -> str:
        request = self.context.get("request")
        if request and request.user:
            return obj.get_title_for_user(request.user)
        return str(obj)

    def get_participant_names(self, obj) -> list:
        return [
            {"id": str(u.id), "name": u.get_display_name()}
            for u in obj.participants.all()
        ]

    def get_last_message(self, obj) -> dict | None:
        msg = obj.last_message
        if msg is None:
            return None
        return {
            "id": str(msg.id),
            "sender_name": msg.sender.get_display_name(),
            "content": msg.content[:100],
            "created_at": msg.created_at,
        }

    def get_unread_count(self, obj) -> int:
        request = self.context.get("request")
        if request and request.user:
            return obj.messages.filter(
                is_read=False
            ).exclude(sender=request.user).count()
        return 0


class ConversationDetailSerializer(ConversationListSerializer):
    """会话详情序列化器（含最近 N 条消息）."""

    messages = serializers.SerializerMethodField()

    class Meta(ConversationListSerializer.Meta):
        fields = ConversationListSerializer.Meta.fields + ["messages"]

    def get_messages(self, obj):
        # 默认返回最近 50 条消息，前端滚动加载更多
        messages = obj.messages.order_by("-created_at")[:50]
        # 反转为正序
        return MessageSerializer(
            reversed(messages), many=True
        ).data


class ConversationCreateSerializer(serializers.ModelSerializer):
    """创建会话序列化器."""

    participant_id = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Conversation
        fields = ["participant_id", "product"]
        extra_kwargs = {
            "product": {"required": False},
        }

    def validate_participant_id(self, value):
        """验证参与者存在."""
        if not User.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("用户不存在或已禁用")
        return value

    def validate(self, attrs):
        """不允许和自己创建会话."""
        request_user = self.context["request"].user
        if str(request_user.id) == str(attrs["participant_id"]):
            raise serializers.ValidationError(
                {"participant_id": "不能和自己创建会话"}
            )
        return attrs
