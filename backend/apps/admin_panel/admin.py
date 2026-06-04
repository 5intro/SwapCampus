"""管理面板 — 跨模块 Django Admin 增强."""

from django.contrib import admin
from django.contrib.auth import get_user_model

from apps.admin_panel.actions import approve_products, ban_users, cancel_orders_admin, hide_products
from apps.products.admin import ProductAdmin
from apps.products.models import Product
from apps.transactions.admin import OrderAdmin
from apps.transactions.models import Order
from apps.users.admin import UserAdmin
from apps.users.models import CreditRecord

User = get_user_model()

# ── 增强 ProductAdmin：注册批量操作 ─────────────────────────
ProductAdmin.actions = list(ProductAdmin.actions) + [
    approve_products,
    hide_products,
]

# ── 增强 UserAdmin：注册批量操作 ───────────────────────────
UserAdmin.actions = list(UserAdmin.actions) + [ban_users]

# ── 增强 OrderAdmin：注册批量操作 ───────────────────────────
OrderAdmin.actions = list(OrderAdmin.actions) + [cancel_orders_admin]

# ── CreditRecord Inline for User ──────────────────────────
class CreditRecordInline(admin.TabularInline):
    model = CreditRecord
    extra = 0
    readonly_fields = ["change", "reason", "score_after", "created_at"]
    fields = ["change", "reason", "description", "score_after", "created_at"]
    ordering = ["-created_at"]
    can_delete = False

# 将积分记录 Inline 添加到 UserAdmin
if CreditRecordInline not in UserAdmin.inlines:
    UserAdmin.inlines = list(UserAdmin.inlines) + [CreditRecordInline]
