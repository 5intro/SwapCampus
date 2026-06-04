"""商品模块 Django Admin 注册."""

from django.contrib import admin

from apps.products.models import Category, Product, ProductImage, Tag


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "seller", "price", "status", "condition", "view_count", "created_at"]
    list_filter = ["status", "condition", "campus", "created_at"]
    search_fields = ["title", "description"]
    raw_id_fields = ["seller", "category"]
    filter_horizontal = ["tags"]
    readonly_fields = ["view_count", "created_at", "updated_at"]
    inlines = [ProductImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "sort_order", "created_at"]
    list_filter = ["parent"]
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "is_cover", "sort_order", "created_at"]
    list_filter = ["is_cover"]
    raw_id_fields = ["product"]
