"""Django Admin 批量操作."""

from django.contrib import messages

from apps.products.models import Product
from apps.transactions.models import Order


def approve_products(modeladmin, request, queryset):
    """批量审核通过商品（将状态改为在售）."""
    count = queryset.update(status=Product.Status.ACTIVE)
    messages.success(request, f"已审核通过 {count} 个商品")


approve_products.short_description = "审核通过（设为在售）"


def hide_products(modeladmin, request, queryset):
    """批量隐藏商品."""
    count = queryset.update(status=Product.Status.HIDDEN)
    messages.success(request, f"已隐藏 {count} 个商品")


hide_products.short_description = "隐藏选中商品"


def ban_users(modeladmin, request, queryset):
    """批量禁用用户."""
    count = queryset.update(is_active=False)
    messages.success(request, f"已禁用 {count} 个用户")


ban_users.short_description = "禁用选中用户"


def cancel_orders_admin(modeladmin, request, queryset):
    """批量取消订单（管理员强制取消）."""
    count = queryset.filter(
        status__in=[
            Order.Status.PENDING,
            Order.Status.ACCEPTED,
            Order.Status.FACE_CONFIRM,
        ]
    ).update(
        status=Order.Status.CANCELLED,
        cancel_reason="管理员取消",
    )
    messages.success(request, f"已取消 {count} 个进行中的订单")


cancel_orders_admin.short_description = "强制取消选中订单"
