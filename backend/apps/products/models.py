"""商品模块模型 — Product, Category, Tag, ProductImage."""

from django.conf import settings
from django.db import models

from core.models import BaseModel


class Category(BaseModel):
    """商品分类.

    支持两级分类，通过 parent 自引用实现父子关系。
    """

    name = models.CharField(max_length=50, verbose_name="分类名称")
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="分类图标",
        help_text="Element Plus 图标名或 emoji",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级分类",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="排序权重")

    class Meta:
        db_table = "categories"
        verbose_name = "商品分类"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "created_at"]
        unique_together = [("name",)]

    def __str__(self) -> str:
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Tag(BaseModel):
    """商品标签."""

    name = models.CharField(max_length=50, unique=True, verbose_name="标签名称")

    class Meta:
        db_table = "tags"
        verbose_name = "商品标签"
        verbose_name_plural = verbose_name
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(BaseModel):
    """商品模型."""

    class Condition(models.TextChoices):
        NEW = "new", "全新"
        LIKE_NEW = "like_new", "几乎全新"
        USED = "used", "使用过"
        OLD = "old", "老旧"

    class Status(models.TextChoices):
        ACTIVE = "active", "在售"
        RESERVED = "reserved", "已预定"
        SOLD = "sold", "已售出"
        HIDDEN = "hidden", "已隐藏"

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="卖家",
    )
    title = models.CharField(max_length=200, verbose_name="商品标题")
    description = models.TextField(max_length=5000, blank=True, verbose_name="商品描述")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="售价")
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="原价",
    )
    condition = models.CharField(
        max_length=10,
        choices=Condition.choices,
        default=Condition.USED,
        verbose_name="成色",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        verbose_name="商品状态",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="所属分类",
    )
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="标签")
    campus = models.CharField(max_length=30, blank=True, verbose_name="所在校区")
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览次数")

    class Meta:
        db_table = "products"
        verbose_name = "商品"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["seller", "-created_at"]),
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def cover_image(self) -> "ProductImage | None":
        """返回封面图（优先 is_cover=True，其次第一张，最后 None）."""
        if not hasattr(self, "_prefetched_images"):
            return self.images.filter(is_cover=True).first() or self.images.first()
        # prefetch 模式下避免额外查询
        images = list(self.images.all())
        for img in images:
            if img.is_cover:
                return img
        return images[0] if images else None


class ProductImage(BaseModel):
    """商品图片."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="所属商品",
    )
    image = models.ImageField(upload_to="products/%Y/%m/", verbose_name="图片文件")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="排序权重")
    is_cover = models.BooleanField(default=False, verbose_name="是否为封面")

    class Meta:
        db_table = "product_images"
        verbose_name = "商品图片"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "created_at"]

    def __str__(self) -> str:
        return f"{self.product.title} 图片 #{self.sort_order}"
