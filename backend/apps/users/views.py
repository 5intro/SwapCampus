"""用户体系 API 视图."""

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from apps.users.models import CreditRecord, Notification
from apps.users.serializers import (
    CreditRecordSerializer,
    NotificationSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from core.utils import build_success_response

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# JWT 视图（包装统一响应格式）
# ═══════════════════════════════════════════════════════════
class TokenObtainPairView(BaseTokenObtainPairView):
    """登录获取 JWT Token.

    POST /api/users/login/

    返回统一格式：
    {
        "success": true,
        "data": {"access": "...", "refresh": "..."},
        "error": null
    }
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # SimpleJWT 返回 {"access": "...", "refresh": "..."}
        # 包装为统一格式
        return Response(
            build_success_response(response.data),
            status=response.status_code,
        )


class TokenRefreshView(BaseTokenRefreshView):
    """刷新 JWT Access Token.

    POST /api/users/token/refresh/

    返回统一格式：
    {
        "success": true,
        "data": {"access": "..."},
        "error": null
    }
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return Response(
            build_success_response(response.data),
            status=response.status_code,
        )


# ═══════════════════════════════════════════════════════════
# 注册
# ═══════════════════════════════════════════════════════════
class RegisterView(APIView):
    """用户注册.

    POST /api/users/register/
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserSerializer},
        description="使用学号注册新用户",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            build_success_response(UserSerializer(user).data),
            status=status.HTTP_201_CREATED,
        )


# ═══════════════════════════════════════════════════════════
# 用户 ViewSet
# ═══════════════════════════════════════════════════════════
@extend_schema_view(
    list=extend_schema(summary="用户列表", description="获取所有用户列表（公开信息）"),
    retrieve=extend_schema(summary="用户详情", description="获取指定用户公开信息"),
)
class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """用户 ViewSet.

    - GET /api/users/ → 用户列表（公开信息）
    - GET /api/users/{id}/ → 用户详情（公开信息）
    - GET /api/users/me/ → 当前登录用户完整信息
    - PATCH /api/users/me/ → 更新当前用户信息
    """

    queryset = User.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action in ("me", "update_me"):
            return UserProfileSerializer
        return UserSerializer

    def get_queryset(self) -> QuerySet:
        """过滤未激活用户（管理后台除外）."""
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs.select_related()

    def retrieve(self, request, *args, **kwargs):
        """包装统一格式的用户详情."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(build_success_response(serializer.data))

    @extend_schema(summary="当前用户信息", description="获取当前登录用户的完整信息")
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """GET /api/users/me/ — 当前用户完整信息."""
        serializer = self.get_serializer(request.user)
        return Response(build_success_response(serializer.data))

    @extend_schema(
        summary="更新当前用户信息",
        description="部分更新当前登录用户的信息（昵称、简介、头像等）",
        request=UserUpdateSerializer,
    )
    @me.mapping.patch
    def update_me(self, request):
        """PATCH /api/users/me/ — 更新当前用户信息."""
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(build_success_response(serializer.data))

    @extend_schema(
        summary="用户信用积分记录",
        description="获取指定用户的信用积分变更记录（仅本人可查看全部，他人仅可查看公开记录）",
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="credit-records",
        permission_classes=[IsAuthenticated],
    )
    def credit_records(self, request, id=None):
        """GET /api/users/{id}/credit-records/ — 积分变更记录."""
        user = self.get_object()
        # 非本人仅可查看好评/差评相关的公开记录
        qs = CreditRecord.objects.filter(user=user)
        if request.user != user and not request.user.is_staff:
            qs = qs.filter(reason__in=["good_review", "bad_review"])

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = CreditRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CreditRecordSerializer(qs, many=True)
        return Response(build_success_response(serializer.data))


class NotificationViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """站内通知 ViewSet.

    - GET    /api/notifications/             → 我的通知列表
    - POST   /api/notifications/{id}/read/   → 标记已读
    - POST   /api/notifications/read-all/    → 全部已读
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"])
    def read(self, request, id=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(build_success_response({"status": "ok"}))

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response(build_success_response({"status": "ok"}))
