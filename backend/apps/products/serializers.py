"""商品模块序列化器."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.products.models import Category, Favorite, Product, ProductImage, Report, Tag
from core.utils import compress_image

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# 分类
# ═══════════════════════════════════════════════════════════
class CategoryChildrenSerializer(serializers.ModelSerializer):
    """分类子级序列化器（避免递归过深，仅一层子级）."""

    class Meta:
        model = Category
        fields = ["id", "name", "icon", "sort_order"]


class CategorySerializer(serializers.ModelSerializer):
    """商品分类序列化器."""

    children = CategoryChildrenSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "icon", "parent", "sort_order", "children", "created_at"]
        read_only_fields = ["id", "created_at"]


# ═══════════════════════════════════════════════════════════
# 标签
# ═══════════════════════════════════════════════════════════
class TagSerializer(serializers.ModelSerializer):
    """商品标签序列化器."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


# ═══════════════════════════════════════════════════════════
# 图片
# ═══════════════════════════════════════════════════════════
class ProductImageSerializer(serializers.ModelSerializer):
    """商品图片序列化器."""

    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_cover", "sort_order"]
        read_only_fields = ["id"]


# ═══════════════════════════════════════════════════════════
# 商品 — 列表
# ═══════════════════════════════════════════════════════════
class ProductListSerializer(serializers.ModelSerializer):
    """商品列表序列化器（精简字段）."""

    cover_image = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    condition_display = serializers.CharField(source="get_condition_display", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "price",
            "original_price",
            "condition",
            "condition_display",
            "status",
            "campus",
            "view_count",
            "cover_image",
            "seller",
            "category",
            "created_at",
        ]

    def get_cover_image(self, obj) -> str | None:
        img = obj.cover_image
        if img and img.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(img.image.url)
            return img.image.url
        return None

    def get_seller(self, obj) -> dict:
        return {
            "id": str(obj.seller.id),
            "nickname": obj.seller.get_display_name(),
            "credit_score": obj.seller.credit_score,
        }

    def get_category(self, obj) -> dict | None:
        if obj.category:
            return {"id": str(obj.category.id), "name": obj.category.name}
        return None


# ═══════════════════════════════════════════════════════════
# 商品 — 详情
# ═══════════════════════════════════════════════════════════
class ProductDetailSerializer(ProductListSerializer):
    """商品详情序列化器（全字段）."""

    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            "description",
            "images",
            "tags",
            "updated_at",
        ]

    def get_seller(self, obj) -> dict:
        return {
            "id": str(obj.seller.id),
            "username": obj.seller.username,
            "nickname": obj.seller.get_display_name(),
            "avatar": self._get_avatar_url(obj.seller),
            "credit_score": obj.seller.credit_score,
            "credit_level": obj.seller.credit_level,
            "campus": obj.seller.campus,
        }

    def _get_avatar_url(self, user) -> str | None:
        if user.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(user.avatar.url)
            return user.avatar.url
        return None


# ═══════════════════════════════════════════════════════════
# 商品 — 创建
# ═══════════════════════════════════════════════════════════
class ProductCreateSerializer(serializers.ModelSerializer):
    """商品创建序列化器."""

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source="tags",
        many=True,
        write_only=True,
        required=False,
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=9,
    )

    class Meta:
        model = Product
        fields = [
            "title",
            "description",
            "price",
            "original_price",
            "condition",
            "campus",
            "category_id",
            "tag_ids",
            "images",
        ]

    def validate_price(self, value):
        if value < 0.01:
            raise serializers.ValidationError("售价不能低于 0.01 元")
        return value

    def validate_original_price(self, value):
        if value is not None and value < 0.01:
            raise serializers.ValidationError("原价不能低于 0.01 元")
        return value

    def validate(self, attrs):
        price = attrs.get("price")
        original_price = attrs.get("original_price")
        if price and original_price and original_price < price:
            raise serializers.ValidationError({"original_price": "原价不能低于售价"})
        return attrs

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        tags_data = validated_data.pop("tags", [])
        product = Product.objects.create(**validated_data)

        if tags_data:
            product.tags.set(tags_data)

        for i, img_file in enumerate(images_data):
            compressed = compress_image(img_file)
            ProductImage.objects.create(
                product=product,
                image=compressed,
                sort_order=i,
                is_cover=(i == 0),
            )

        return product


# ═══════════════════════════════════════════════════════════
# 商品 — 更新
# ═══════════════════════════════════════════════════════════
class ProductUpdateSerializer(serializers.ModelSerializer):
    """商品更新序列化器（全部可选）."""

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source="tags",
        many=True,
        write_only=True,
        required=False,
    )
    new_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=9,
    )

    class Meta:
        model = Product
        fields = [
            "title",
            "description",
            "price",
            "original_price",
            "condition",
            "status",
            "campus",
            "category_id",
            "tag_ids",
            "new_images",
        ]
        extra_kwargs = {
            "title": {"required": False},
            "price": {"required": False},
        }

    def validate_price(self, value):
        if value is not None and value < 0.01:
            raise serializers.ValidationError("售价不能低于 0.01 元")
        return value

    def validate_original_price(self, value):
        if value is not None and value < 0.01:
            raise serializers.ValidationError("原价不能低于 0.01 元")
        return value

    def update(self, instance, validated_data):
        new_images = validated_data.pop("new_images", [])
        instance = super().update(instance, validated_data)

        if new_images:
            # 追加新图片，第一张设为封面如果还没有封面
            current_count = instance.images.count()
            for i, img_file in enumerate(new_images):
                compressed = compress_image(img_file)
                is_cover = (current_count == 0 and i == 0)
                ProductImage.objects.create(
                    product=instance,
                    image=compressed,
                    sort_order=current_count + i,
                    is_cover=is_cover,
                )

        return instance


# ═══════════════════════════════════════════════════════════
# 收藏
# ═══════════════════════════════════════════════════════════
class FavoriteSerializer(serializers.ModelSerializer):
    """收藏序列化器."""

    product = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ["id", "product", "created_at"]
        read_only_fields = ["id", "created_at"]

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
            "status": obj.product.status,
            "cover_image": img_url,
        }


class FavoriteCreateSerializer(serializers.Serializer):
    """收藏创建序列化器."""

    product_id = serializers.UUIDField()


# ═══════════════════════════════════════════════════════════
# 举报
# ═══════════════════════════════════════════════════════════
class ReportSerializer(serializers.ModelSerializer):
    """举报序列化器."""

    reporter_name = serializers.SerializerMethodField()
    product_title = serializers.SerializerMethodField()
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id", "product", "product_title", "reporter", "reporter_name",
            "reason", "reason_display", "description", "status",
            "status_display", "handled_note", "created_at",
        ]
        read_only_fields = ["id", "status", "handled_by", "handled_note", "created_at"]

    def get_reporter_name(self, obj) -> str:
        return obj.reporter.get_display_name()

    def get_product_title(self, obj) -> str:
        return obj.product.title


class ReportCreateSerializer(serializers.Serializer):
    """举报创建序列化器."""

    product_id = serializers.UUIDField()
    reason = serializers.ChoiceField(choices=[
        ("inappropriate", "内容不当"),
        ("counterfeit", "假冒伪劣"),
        ("fraud", "虚假交易"),
        ("prohibited", "违禁物品"),
        ("other", "其他"),
    ])
    description = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
