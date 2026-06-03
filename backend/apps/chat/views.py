"""站内通讯 REST API 视图."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.chat.models import Conversation, Message
from apps.chat.serializers import (
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationListSerializer,
    MessageSerializer,
)
from core.utils import build_success_response

User = get_user_model()


@extend_schema_view(
    list=extend_schema(summary="会话列表", description="获取当前用户的所有会话"),
    create=extend_schema(summary="创建会话", description="创建或获取与指定用户的会话"),
    retrieve=extend_schema(summary="会话详情", description="获取会话详情和最近消息"),
)
class ConversationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """会话 ViewSet.

    - GET  /api/chat/conversations/ → 我的会话列表
    - POST /api/chat/conversations/ → 创建/获取会话
    - GET  /api/chat/conversations/{id}/ → 会话详情 + 最近消息
    - GET  /api/chat/conversations/{id}/messages/ → 分页获取消息
    - POST /api/chat/conversations/{id}/read/ → 标记已读
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action == "create":
            return ConversationCreateSerializer
        if self.action == "retrieve":
            return ConversationDetailSerializer
        return ConversationListSerializer

    def get_queryset(self) -> QuerySet:
        """仅返回当前用户参与的会话，预加载参与者和最后消息."""
        user = self.request.user
        return (
            Conversation.objects.filter(participants=user)
            .prefetch_related("participants", "messages")
            .annotate(
                # 预计算未读消息数（排除自己发的）
                unread=Count(
                    "messages",
                    filter=~Q(messages__sender=user) & Q(messages__is_read=False),
                )
            )
            .distinct()
        )

    def perform_create(self, serializer):
        """创建会话：如果两人之间已有会话则复用，否则新建."""
        participant_id = serializer.validated_data.pop("participant_id")
        product = serializer.validated_data.get("product")
        user = self.request.user
        other = User.objects.get(id=participant_id)

        # 查找已有会话（不限定 product，避免创建重复会话）
        existing = (
            Conversation.objects.filter(participants=user)
            .filter(participants=other)
            .first()
        )
        if existing:
            # 如果要关联商品且现有会话未关联，则更新关联
            if product and not existing.product:
                existing.product = product
                existing.save(update_fields=["product", "updated_at"])
            serializer.instance = existing
            return

        conversation = Conversation.objects.create(product=product)
        conversation.participants.add(user, other)
        serializer.instance = conversation

    @extend_schema(
        summary="获取消息列表",
        description="分页获取指定会话的历史消息（按时间正序，最新消息在前）",
    )
    @action(detail=True, methods=["get"], url_path="messages")
    def list_messages(self, request, id=None):
        """GET /api/chat/conversations/{id}/messages/ — 分页获取消息."""
        conversation = self.get_object()
        qs = conversation.messages.order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MessageSerializer(qs, many=True)
        return Response(build_success_response(serializer.data))

    @extend_schema(
        summary="发送消息",
        description="向会话发送一条新消息（REST 方式，WebSocket 更推荐）",
        request=MessageSerializer,
    )
    @list_messages.mapping.post
    def send_message(self, request, id=None):
        """POST /api/chat/conversations/{id}/messages/ — 发送消息."""
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = serializer.save(
            conversation=conversation,
            sender=request.user,
        )
        # 发送后自动刷新会话的 updated_at
        conversation.save(update_fields=["updated_at"])
        return Response(
            build_success_response(MessageSerializer(msg).data),
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="标记已读",
        description="将指定会话中所有未读消息标记为已读",
    )
    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, id=None):
        """POST /api/chat/conversations/{id}/read/ — 标记已读."""
        conversation = self.get_object()
        count = (
            conversation.messages.filter(is_read=False)
            .exclude(sender=request.user)
            .update(is_read=True)
        )
        return Response(
            build_success_response({"marked_read": count}),
            status=status.HTTP_200_OK,
        )
