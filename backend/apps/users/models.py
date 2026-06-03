"""用户体系模型.

- User：自定义用户模型，扩展 AbstractUser
- CreditRecord：信用积分变更记录
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from core.models import BaseModel


class User(AbstractUser):
    """自定义用户模型.

    在 Django AbstractUser 基础上扩展校园业务字段。
    使用 username 存储学号（全校唯一标识），email 可选。
    """

    # ── 基础字段覆盖 ──────────────────────────────────────
    # username → 学号（北京林业大学学号，8 位数字）
    # AbstractUser 自带 username, password, email, first_name, last_name,
    # is_active, is_staff, is_superuser, date_joined

    # ── 扩展字段 ──────────────────────────────────────────
    nickname = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="昵称",
        help_text="用户自定义显示名称，默认使用学号",
    )
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="头像",
    )
    credit_score = models.IntegerField(
        default=100,
        db_index=True,
        verbose_name="信用分",
        help_text="初始 100 分，根据交易行为增减",
    )
    campus = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="校区",
        help_text="如：校本部、鹫峰校区",
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="个人简介",
    )

    class Meta:
        db_table = "users"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return f"{self.get_display_name()} ({self.username})"

    def get_display_name(self) -> str:
        """获取用户对外显示名称：昵称 > 学号."""
        return self.nickname or self.username

    @property
    def credit_level(self) -> str:
        """信用等级（基于信用分）."""
        if self.credit_score >= 150:
            return "excellent"
        elif self.credit_score >= 100:
            return "good"
        elif self.credit_score >= 60:
            return "fair"
        else:
            return "poor"


class CreditRecord(BaseModel):
    """信用积分变更记录.

    每次交易评价后记录积分变动，可追溯用户信用历史。
    """

    class ChangeReason(models.TextChoices):
        ORDER_COMPLETE = "order_complete", "交易完成"
        GOOD_REVIEW = "good_review", "获得好评"
        BAD_REVIEW = "bad_review", "获得差评"
        CANCEL_ORDER = "cancel_order", "取消订单"
        VIOLATION = "violation", "违规处罚"
        APPEAL_RESTORE = "appeal_restore", "申诉恢复"
        INITIAL = "initial", "初始积分"
        OTHER = "other", "其他"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="credit_records",
        verbose_name="用户",
    )
    change = models.IntegerField(
        verbose_name="积分变化",
        help_text="正数为加分，负数为减分",
    )
    reason = models.CharField(
        max_length=20,
        choices=ChangeReason.choices,
        verbose_name="变更原因",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="详细说明",
    )
    score_after = models.IntegerField(
        verbose_name="变更后积分",
        help_text="记录本次变更后的积分值，便于审计",
    )
    related_order = models.ForeignKey(
        "transactions.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credit_changes",
        verbose_name="关联订单",
    )

    class Meta:
        db_table = "credit_records"
        verbose_name = "信用积分记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self) -> str:
        sign = "+" if self.change >= 0 else ""
        return f"{self.user.username} {sign}{self.change} ({self.reason})"
