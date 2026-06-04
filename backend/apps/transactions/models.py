"""交易模块模型 — Order, Review, FaceConfirm."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import BaseModel


class Order(BaseModel):
    """订单模型.

    状态流转：pending → accepted/rejected/cancelled → face_confirm → completed
    """

    class Status(models.TextChoices):
        PENDING = "pending", "等待卖家确认"
        ACCEPTED = "accepted", "已接受，待面交"
        REJECTED = "rejected", "已拒绝"
        CANCELLED = "cancelled", "已取消"
        FACE_CONFIRM = "face_confirm", "面交确认中"
        COMPLETED = "completed", "已完成"

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchases",
        verbose_name="买家",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sales",
        verbose_name="卖家",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="商品",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="订单状态",
    )
    meet_time = models.DateTimeField(null=True, blank=True, verbose_name="约定面交时间")
    meet_location = models.CharField(max_length=200, blank=True, verbose_name="面交地点")
    cancel_reason = models.CharField(max_length=500, blank=True, verbose_name="取消原因")
    cancel_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_orders",
        verbose_name="取消人",
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    buyer_rated = models.BooleanField(default=False, verbose_name="买家已评价")
    seller_rated = models.BooleanField(default=False, verbose_name="卖家已评价")

    class Meta:
        db_table = "orders"
        verbose_name = "订单"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["buyer", "status"]),
            models.Index(fields=["seller", "status"]),
        ]

    def __str__(self) -> str:
        return f"Order {self.id.hex[:8]}: {self.product.title}"


class Review(BaseModel):
    """交易评价.

    每笔订单双方可互评一次，评价后触发对方信用分变更。
    """

    class ReviewType(models.TextChoices):
        BUYER_TO_SELLER = "buyer_to_seller", "买家评价卖家"
        SELLER_TO_BUYER = "seller_to_buyer", "卖家评价买家"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="关联订单",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_given",
        verbose_name="评价人",
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_received",
        verbose_name="被评价人",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="评分",
    )
    content = models.TextField(max_length=500, blank=True, verbose_name="评价内容")
    review_type = models.CharField(
        max_length=20,
        choices=ReviewType.choices,
        verbose_name="评价类型",
    )

    class Meta:
        db_table = "reviews"
        verbose_name = "交易评价"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        unique_together = [("order", "reviewer")]

    def __str__(self) -> str:
        return f"{self.reviewer.get_display_name()} → {self.reviewee.get_display_name()} ({self.rating}★)"


class FaceConfirm(BaseModel):
    """面交确认.

    卖家生成6位确认码，买家在面交时输入确认码验证，完成交易。
    """

    class Status(models.TextChoices):
        PENDING = "pending", "待确认"
        CONFIRMED = "confirmed", "已确认"
        EXPIRED = "expired", "已过期"

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="face_confirm",
        verbose_name="关联订单",
    )
    confirm_code = models.CharField(max_length=6, verbose_name="确认码")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="face_confirms_created",
        verbose_name="生成人（卖家）",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="face_confirms_received",
        verbose_name="确认人（买家）",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="确认状态",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="确认时间")

    class Meta:
        db_table = "face_confirms"
        verbose_name = "面交确认"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"面交确认 #{self.confirm_code}"
