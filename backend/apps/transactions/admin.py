"""交易模块 Django Admin 注册."""

from django.contrib import admin

from apps.transactions.models import FaceConfirm, Order, Review


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1
    readonly_fields = ["created_at"]


class FaceConfirmInline(admin.TabularInline):
    model = FaceConfirm
    extra = 0
    readonly_fields = ["confirm_code", "created_at", "confirmed_at"]
    fields = ["confirm_code", "status", "created_by", "confirmed_by", "confirmed_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id_short",
        "buyer",
        "seller",
        "product",
        "status",
        "meet_time",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = [
        "buyer__username",
        "buyer__nickname",
        "seller__username",
        "seller__nickname",
        "product__title",
    ]
    raw_id_fields = ["buyer", "seller", "product", "cancel_by"]
    readonly_fields = ["created_at", "updated_at", "completed_at"]
    inlines = [ReviewInline, FaceConfirmInline]

    @admin.display(description="订单号")
    def id_short(self, obj):
        return obj.id.hex[:8]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "order_short", "reviewer", "reviewee", "rating", "review_type", "created_at"]
    list_filter = ["rating", "review_type", "created_at"]
    search_fields = ["reviewer__nickname", "reviewee__nickname", "content"]
    raw_id_fields = ["order", "reviewer", "reviewee"]

    @admin.display(description="订单号")
    def order_short(self, obj):
        return obj.order.id.hex[:8]


@admin.register(FaceConfirm)
class FaceConfirmAdmin(admin.ModelAdmin):
    list_display = ["id", "order_short", "status", "created_by", "confirmed_by", "created_at"]
    list_filter = ["status"]
    raw_id_fields = ["order", "created_by", "confirmed_by"]
    readonly_fields = ["created_at", "confirmed_at"]

    @admin.display(description="订单号")
    def order_short(self, obj):
        return obj.order.id.hex[:8]
