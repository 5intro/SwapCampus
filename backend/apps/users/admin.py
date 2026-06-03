"""用户体系 Django Admin 配置."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.users.models import CreditRecord, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """自定义用户 Admin.

    扩展 Django 默认 UserAdmin，加入学号、信用分、校区等字段。
    """

    list_display = [
        "username",
        "nickname",
        "email",
        "credit_score",
        "campus",
        "is_active",
        "is_staff",
        "date_joined",
    ]
    list_filter = ["is_active", "is_staff", "campus", "date_joined"]
    search_fields = ["username", "nickname", "email"]
    ordering = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (_("校园信息"), {"fields": ("nickname", "avatar", "credit_score", "campus", "bio")}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_("校园信息"), {"fields": ("nickname", "campus")}),
    )


@admin.register(CreditRecord)
class CreditRecordAdmin(admin.ModelAdmin):
    """信用积分记录 Admin."""

    list_display = [
        "user",
        "change",
        "reason",
        "score_after",
        "created_at",
    ]
    list_filter = ["reason", "created_at"]
    search_fields = ["user__username", "user__nickname", "description"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    raw_id_fields = ["user", "related_order"]
