"""交易模块 API 视图."""

from django.db.models import Q, QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.transactions.models import Order, Review
from apps.transactions.serializers import (
    FaceConfirmSerializer,
    FaceConfirmVerifySerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
)
from apps.transactions.services import create_face_confirm, create_review, transition_order, verify_face_confirm
from apps.users.services import create_notification
from core.utils import build_success_response


@extend_schema_view(
    list=extend_schema(summary="订单列表", description="获取当前用户的订单（作为买家或卖家）"),
    create=extend_schema(summary="创建订单", description="买家对商品发起购买请求"),
    retrieve=extend_schema(summary="订单详情", description="获取订单完整信息"),
)
class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """订单 ViewSet.

    - GET    /api/transactions/orders/ → 我的订单列表
    - POST   /api/transactions/orders/ → 创建订单
    - GET    /api/transactions/orders/{id}/ → 订单详情
    - POST   /api/transactions/orders/{id}/accept/ → 卖家接受
    - POST   /api/transactions/orders/{id}/reject/ → 卖家拒绝
    - POST   /api/transactions/orders/{id}/cancel/ → 取消订单
    - POST   /api/transactions/orders/{id}/face_confirm/ → 生成/验证面交确认码
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderListSerializer

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        qs = (
            Order.objects.filter(Q(buyer=user) | Q(seller=user))
            .select_related("buyer", "seller", "product", "face_confirm")
            .prefetch_related("product__images")
        )
        # 支持按状态筛选（逗号分隔多个状态）
        status_param = self.request.query_params.get("status", "")
        if status_param:
            statuses = [s.strip() for s in status_param.split(",") if s.strip()]
            if statuses:
                qs = qs.filter(status__in=statuses)
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(build_success_response(serializer.data))

    def perform_create(self, serializer):
        order = serializer.save()
        create_notification(
            order.seller, "new_order",
            "新订单",
            f"{self.request.user.get_display_name()} 购买了《{order.product.title}》",
            related_order=order, related_product=order.product,
        )
        return order

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output = OrderDetailSerializer(serializer.instance, context={"request": request})
        return Response(
            build_success_response(output.data),
            status=status.HTTP_201_CREATED,
        )

    def check_object_permissions(self, request, obj):
        """仅买卖双方可访问订单."""
        if obj.buyer_id != request.user.id and obj.seller_id != request.user.id:
            self.permission_denied(request)

    def _handle_service_error(self, error_msg: str, status_code=400):
        return Response(
            {"success": False, "data": None, "error": {"code": "BAD_REQUEST", "message": error_msg}},
            status=status_code,
        )

    @extend_schema(summary="接受订单", description="卖家接受订单")
    @action(detail=True, methods=["post"])
    def accept(self, request, id=None):
        order = self.get_object()
        if request.user.id != order.seller_id:
            self.permission_denied(request)
        try:
            order = transition_order(order, Order.Status.ACCEPTED, request.user)
        except ValueError as e:
            return self._handle_service_error(str(e))
        return Response(build_success_response({"status": order.status}))

    @extend_schema(summary="拒绝订单", description="卖家拒绝订单")
    @action(detail=True, methods=["post"])
    def reject(self, request, id=None):
        order = self.get_object()
        if request.user.id != order.seller_id:
            self.permission_denied(request)
        reason = request.data.get("reason", "")
        try:
            order = transition_order(order, Order.Status.REJECTED, request.user, cancel_reason=reason)
        except ValueError as e:
            return self._handle_service_error(str(e))
        return Response(build_success_response({"status": order.status}))

    @extend_schema(summary="取消订单", description="买家或卖家取消订单")
    @action(detail=True, methods=["post"])
    def cancel(self, request, id=None):
        order = self.get_object()
        reason = request.data.get("reason", "")
        try:
            order = transition_order(
                order,
                Order.Status.CANCELLED,
                request.user,
                cancel_reason=reason,
            )
        except ValueError as e:
            return self._handle_service_error(str(e))
        return Response(build_success_response({"status": order.status}))

    @extend_schema(
        summary="面交确认",
        description="GET: 生成确认码（卖家）, POST: 验证确认码（买家）",
    )
    @action(detail=True, methods=["get", "post"])
    def face_confirm(self, request, id=None):
        order = self.get_object()

        if request.method == "GET":
            try:
                fc = create_face_confirm(order, request.user)
            except ValueError as e:
                return self._handle_service_error(str(e))
            serializer = FaceConfirmSerializer(fc)
            data = serializer.data
            data["confirm_code"] = fc.confirm_code
            return Response(build_success_response(data))

        # POST: 买家验证确认码
        verify_serializer = FaceConfirmVerifySerializer(data=request.data)
        verify_serializer.is_valid(raise_exception=True)
        code = verify_serializer.validated_data["code"]

        try:
            order = verify_face_confirm(order, code, request.user)
        except ValueError as e:
            return self._handle_service_error(str(e))
        return Response(build_success_response({"status": order.status}))


@extend_schema_view(
    list=extend_schema(summary="评价列表", description="获取评价列表，支持按被评价人/订单筛选"),
    create=extend_schema(summary="创建评价", description="对已完成订单进行评价"),
)
class ReviewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """评价 ViewSet.

    - GET    /api/transactions/reviews/ → 评价列表
    - POST   /api/transactions/reviews/ → 创建评价
    - GET    /api/transactions/reviews/{id}/ → 评价详情
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset().select_related("reviewer", "reviewee", "order")
        reviewee = self.request.query_params.get("reviewee")
        order_id = self.request.query_params.get("order")
        if reviewee:
            qs = qs.filter(reviewee_id=reviewee)
        if order_id:
            qs = qs.filter(order_id=order_id)
        return qs

    def create(self, request, *args, **kwargs):
        create_serializer = ReviewCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)

        order_id = create_serializer.validated_data["order_id"]
        rating = create_serializer.validated_data["rating"]
        content = create_serializer.validated_data.get("content", "")

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                build_success_response(None),
                status=status.HTTP_404_NOT_FOUND,
            )

        # 权限检查
        if request.user.id not in (order.buyer_id, order.seller_id):
            self.permission_denied(request)

        try:
            review = create_review(order, request.user, rating, content)
        except ValueError as e:
            return Response(
                {"success": False, "data": None, "error": {"code": "BAD_REQUEST", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        output = ReviewSerializer(review, context={"request": request})
        return Response(
            build_success_response(output.data),
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(build_success_response(serializer.data))
