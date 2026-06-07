"""商品模块 API 视图."""

from django.db.models import F, QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.products.filters import ProductFilter
from apps.products.models import Category, Favorite, Product, Report, Tag
from apps.products.serializers import (
    CategorySerializer,
    FavoriteCreateSerializer,
    FavoriteSerializer,
    ProductCreateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductUpdateSerializer,
    ReportCreateSerializer,
    ReportSerializer,
    TagSerializer,
)
from apps.products.services import change_product_status
from core.permissions import IsOwner
from core.utils import build_success_response


@extend_schema_view(
    list=extend_schema(summary="商品列表", description="分页获取商品列表，支持筛选、排序和搜索"),
    create=extend_schema(summary="发布商品", description="发布一个新商品，可附带图片"),
    retrieve=extend_schema(summary="商品详情", description="获取商品完整信息"),
    update=extend_schema(summary="更新商品", description="完整更新商品信息（仅卖家）"),
    partial_update=extend_schema(summary="部分更新商品", description="部分更新商品信息（仅卖家）"),
    destroy=extend_schema(summary="删除商品", description="删除商品（仅卖家）"),
)
class ProductViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """商品 ViewSet.

    - GET    /api/products/ → 商品列表（筛选+搜索+排序）
    - POST   /api/products/ → 发布商品
    - GET    /api/products/{id}/ → 商品详情
    - PATCH  /api/products/{id}/ → 更新商品
    - DELETE /api/products/{id}/ → 删除商品
    - GET    /api/products/my/ → 我的商品
    - POST   /api/products/{id}/mark_reserved/ → 标记已预定
    - POST   /api/products/{id}/mark_sold/ → 标记已售出
    - POST   /api/products/{id}/mark_active/ → 重新上架
    """

    queryset = Product.objects.all()
    filterset_class = ProductFilter
    lookup_field = "id"
    search_fields = ["title", "description"]

    def get_serializer_class(self):
        if self.action in ("create",):
            return ProductCreateSerializer
        if self.action in ("update", "partial_update"):
            return ProductUpdateSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy",
                           "mark_reserved", "mark_sold", "mark_active"):
            return [IsAuthenticated(), IsOwner()]
        if self.action in ("create", "my"):
            return [IsAuthenticated()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        user = self.request.user
        # 未登录 / 非卖家 / 非管理员 → 只显示在售商品
        if not user.is_authenticated or not user.is_staff:
            if self.action == "list":
                qs = qs.filter(status=Product.Status.ACTIVE)
        return qs.select_related("seller", "category").prefetch_related("images", "tags")

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 原子自增浏览次数
        Product.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(build_success_response(serializer.data))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output = ProductDetailSerializer(serializer.instance, context={"request": request})
        return Response(
            build_success_response(output.data),
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output = ProductDetailSerializer(serializer.instance, context={"request": request})
        return Response(build_success_response(output.data))

    def check_object_permissions(self, request, obj):
        """使用 seller 作为 owner 字段进行权限检查."""
        # IsOwner 检查 obj.user，但 Product 用 seller
        # 重写以映射到正确的字段
        for permission in self.get_permissions():
            if isinstance(permission, IsOwner):
                if not (obj.seller == request.user):
                    self.permission_denied(request)
            elif not permission.has_object_permission(request, self, obj):
                self.permission_denied(request)

    @extend_schema(summary="我的商品", description="获取当前用户发布的商品列表")
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my(self, request):
        """GET /api/products/my/ — 我的商品."""
        qs = self.get_queryset().filter(seller=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(qs, many=True, context={"request": request})
        return Response(build_success_response(serializer.data))

    @extend_schema(summary="标记已预定", description="将商品状态改为「已预定」（仅卖家）")
    @action(detail=True, methods=["post"])
    def mark_reserved(self, request, id=None):
        product = self.get_object()
        change_product_status(product, Product.Status.RESERVED)
        return Response(build_success_response({"status": product.status}))

    @extend_schema(summary="标记已售出", description="将商品状态改为「已售出」（仅卖家）")
    @action(detail=True, methods=["post"])
    def mark_sold(self, request, id=None):
        product = self.get_object()
        change_product_status(product, Product.Status.SOLD)
        return Response(build_success_response({"status": product.status}))

    @extend_schema(summary="重新上架", description="将商品状态改为「在售」（仅卖家）")
    @action(detail=True, methods=["post"])
    def mark_active(self, request, id=None):
        product = self.get_object()
        change_product_status(product, Product.Status.ACTIVE)
        return Response(build_success_response({"status": product.status}))

    @extend_schema(summary="相关商品推荐", description="获取与指定商品相关的其他在售商品")
    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def related(self, request, id=None):
        product = self.get_object()
        qs = (
            Product.objects.filter(status=Product.Status.ACTIVE)
            .exclude(id=product.id)
            .filter(category=product.category)
            .select_related("seller", "category")
            .prefetch_related("images", "tags")
        )
        count = qs.count()
        if count < 4:
            # 同分类不足，补充最新商品
            fallback = (
                Product.objects.filter(status=Product.Status.ACTIVE)
                .exclude(id=product.id)
                .exclude(category=product.category)
                .select_related("seller", "category")
                .prefetch_related("images", "tags")
                .order_by("-created_at")[:4]
            )
            qs = list(qs) + list(fallback)
            serializer = ProductListSerializer(qs[:6], many=True, context={"request": request})
        else:
            serializer = ProductListSerializer(qs[:6], many=True, context={"request": request})
        return Response(build_success_response(serializer.data))


@extend_schema_view(
    list=extend_schema(summary="分类列表", description="获取所有商品分类（含子级）"),
    retrieve=extend_schema(summary="分类详情", description="获取指定分类信息"),
)
class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """商品分类 ViewSet（只读）."""

    queryset = Category.objects.filter(parent__isnull=True).prefetch_related("children")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(build_success_response(serializer.data))


@extend_schema_view(
    list=extend_schema(summary="标签列表", description="获取所有商品标签"),
)
class TagViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """商品标签 ViewSet（只读）."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class FavoriteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """收藏 ViewSet.

    - GET    /api/products/favorites/       → 我的收藏列表
    - POST   /api/products/favorites/       → 添加收藏
    - DELETE /api/products/favorites/{id}/  → 取消收藏
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action == "create":
            return FavoriteCreateSerializer
        return FavoriteSerializer

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related("product")
            .prefetch_related("product__images")
        )

    def create(self, request, *args, **kwargs):
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data["product_id"]

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"success": False, "error": {"message": "商品不存在"}},
                status=status.HTTP_404_NOT_FOUND,
            )

        fav, created = Favorite.objects.get_or_create(
            user=request.user, product=product
        )
        if not created:
            # Already favorited, return it as success
            output = FavoriteSerializer(fav, context={"request": request})
            return Response(build_success_response(output.data))

        output = FavoriteSerializer(fav, context={"request": request})
        return Response(
            build_success_response(output.data),
            status=status.HTTP_201_CREATED,
        )

    def check_object_permissions(self, request, obj):
        if obj.user_id != request.user.id:
            self.permission_denied(request)


class ReportViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """举报 ViewSet.

    - POST /api/products/reports/ → 举报商品
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ReportCreateSerializer
        return ReportSerializer

    def create(self, request, *args, **kwargs):
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"success": False, "error": {"message": "商品不存在"}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if product.seller == request.user:
            return Response(
                {"success": False, "error": {"message": "不能举报自己的商品"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report = Report.objects.create(
            reporter=request.user,
            product=product,
            reason=serializer.validated_data["reason"],
            description=serializer.validated_data.get("description", ""),
        )
        output = ReportSerializer(report, context={"request": request})
        return Response(
            build_success_response(output.data),
            status=status.HTTP_201_CREATED,
        )
