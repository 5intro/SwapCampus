"""交易模块序列化器."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.transactions.models import FaceConfirm, Order, Review

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# 订单 — 列表
# ═══════════════════════════════════════════════════════════
class OrderListSerializer(serializers.ModelSerializer):
    """订单列表序列化器（精简）."""

    buyer = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    face_confirm_code = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "product",
            "buyer",
            "seller",
            "status",
            "status_display",
            "meet_time",
            "meet_location",
            "cancel_reason",
            "cancel_by",
            "face_confirm_code",
            "created_at",
        ]

    def get_face_confirm_code(self, obj) -> str | None:
        fc = getattr(obj, "face_confirm", None)
        if fc:
            return fc.confirm_code
        return None

    def get_cancel_by(self, obj) -> str | None:
        if obj.cancel_by:
            return obj.cancel_by.get_display_name()
        return None

    def get_buyer(self, obj) -> dict:
        return {"id": str(obj.buyer.id), "nickname": obj.buyer.get_display_name()}

    def get_seller(self, obj) -> dict:
        return {"id": str(obj.seller.id), "nickname": obj.seller.get_display_name()}

    def get_product(self, obj) -> dict:
        img = obj.product.cover_image
        img_url = None
        if img and img.image:
            request = self.context.get("request")
            if request:
                img_url = request.build_absolute_uri(img.image.url)
        return {
            "id": str(obj.product.id),
            "title": obj.product.title,
            "price": str(obj.product.price),
            "cover_image": img_url,
        }


# ═══════════════════════════════════════════════════════════
# 订单 — 详情
# ═══════════════════════════════════════════════════════════
class OrderDetailSerializer(OrderListSerializer):
    """订单详情序列化器（完整信息）."""

    face_confirm_status = serializers.SerializerMethodField()

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + [
            "cancel_reason",
            "cancel_by",
            "completed_at",
            "buyer_rated",
            "seller_rated",
            "face_confirm_status",
            "updated_at",
        ]

    def get_face_confirm_status(self, obj) -> str | None:
        fc = getattr(obj, "face_confirm", None)
        if fc:
            return fc.status
        return None

    def get_buyer(self, obj) -> dict:
        return {
            "id": str(obj.buyer.id),
            "nickname": obj.buyer.get_display_name(),
            "credit_score": obj.buyer.credit_score,
        }

    def get_seller(self, obj) -> dict:
        return {
            "id": str(obj.seller.id),
            "nickname": obj.seller.get_display_name(),
            "credit_score": obj.seller.credit_score,
        }


# ═══════════════════════════════════════════════════════════
# 订单 — 创建
# ═══════════════════════════════════════════════════════════
class OrderCreateSerializer(serializers.ModelSerializer):
    """订单创建序列化器."""

    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Order
        fields = ["product_id", "meet_time", "meet_location"]
        extra_kwargs = {
            "meet_time": {"required": False},
            "meet_location": {"required": False},
        }

    def validate_product_id(self, value):
        from apps.products.models import Product

        try:
            product = Product.objects.select_related("seller").get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("商品不存在")

        if product.status != Product.Status.ACTIVE:
            raise serializers.ValidationError("该商品当前不可购买")

        request_user = self.context["request"].user
        if product.seller == request_user:
            raise serializers.ValidationError("不能购买自己的商品")

        # 检查是否已有未完成的订单
        if Order.objects.filter(
            product=product,
            buyer=request_user,
            status__in=[Order.Status.PENDING, Order.Status.ACCEPTED, Order.Status.FACE_CONFIRM],
        ).exists():
            raise serializers.ValidationError("您已有一个进行中的订单")

        self._validated_product = product
        return value

    def create(self, validated_data):
        validated_data.pop("product_id")
        product = self._validated_product
        request_user = self.context["request"].user

        order = Order.objects.create(
            buyer=request_user,
            seller=product.seller,
            product=product,
            status=Order.Status.PENDING,
            **validated_data,
        )

        # 商品标记为已预定
        from apps.products.models import Product

        Product.objects.filter(pk=product.pk).update(status=Product.Status.RESERVED)

        return order


# ═══════════════════════════════════════════════════════════
# 评价
# ═══════════════════════════════════════════════════════════
class ReviewSerializer(serializers.ModelSerializer):
    """交易评价序列化器."""

    reviewer_name = serializers.SerializerMethodField(read_only=True)
    reviewee_name = serializers.SerializerMethodField(read_only=True)
    review_type_display = serializers.CharField(source="get_review_type_display", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "order",
            "reviewer",
            "reviewer_name",
            "reviewee",
            "reviewee_name",
            "rating",
            "content",
            "review_type",
            "review_type_display",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "order",
            "reviewer",
            "reviewee",
            "review_type",
            "created_at",
        ]

    def get_reviewer_name(self, obj) -> str:
        return obj.reviewer.get_display_name()

    def get_reviewee_name(self, obj) -> str:
        return obj.reviewee.get_display_name()

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("评分必须在 1-5 之间")
        return value


class ReviewCreateSerializer(serializers.Serializer):
    """评价创建序列化器（仅接收必要字段）."""

    order_id = serializers.UUIDField(write_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    content = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


# ═══════════════════════════════════════════════════════════
# 面交确认
# ═══════════════════════════════════════════════════════════
class FaceConfirmSerializer(serializers.ModelSerializer):
    """面交确认序列化器."""

    class Meta:
        model = FaceConfirm
        fields = [
            "id",
            "order",
            "confirm_code",
            "created_by",
            "confirmed_by",
            "status",
            "created_at",
            "confirmed_at",
        ]
        read_only_fields = [
            "id",
            "order",
            "created_by",
            "confirmed_by",
            "status",
            "created_at",
            "confirmed_at",
        ]


class FaceConfirmVerifySerializer(serializers.Serializer):
    """面交确认码验证序列化器."""

    code = serializers.CharField(max_length=6, min_length=6)
