"""商品模块 API 路由."""

from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.products.views import CategoryViewSet, ProductViewSet, TagViewSet

# 分类路由放在前面，避免 product-detail 的 {id} 模式捕获 "categories"
category_router = SimpleRouter()
category_router.register(r"categories", CategoryViewSet, basename="category")

product_router = SimpleRouter()
product_router.register(r"", ProductViewSet, basename="product")

urlpatterns = [
    path("tags/", TagViewSet.as_view({"get": "list"}), name="tag-list"),
]

# 分类 URL 必须在 product URL 之前，否则 product-detail 的 {id} 会匹配 categories/
urlpatterns += category_router.urls + product_router.urls
