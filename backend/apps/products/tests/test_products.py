"""M2+M3 商品模块单元测试.

测试覆盖：
- 商品 CRUD
- 商品列表筛选/搜索/排序
- 商品状态转换
- 分类/标签 API
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.products.models import Category, Product, ProductImage, Tag


# ── 商品创建 ──────────────────────────────────────────────
class TestProductCreate:
    def test_create_product_success(self, auth_client, category, db):
        """正常发布商品应返回 201."""
        url = reverse("product-list")
        data = {
            "title": "编程入门书籍",
            "description": "九五成新，无笔记",
            "price": 25.50,
            "condition": "like_new",
            "campus": "校本部",
            "category_id": str(category.id),
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["title"] == "编程入门书籍"

    def test_create_product_unauthenticated(self, api_client, db):
        """未登录无法发布商品."""
        url = reverse("product-list")
        response = api_client.post(url, {"title": "test"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_product_negative_price(self, auth_client, category, db):
        """价格不能为负数."""
        url = reverse("product-list")
        data = {"title": "测试", "price": -10, "category_id": str(category.id)}
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_product_original_price_less_than_price(self, auth_client, category, db):
        """原价不能低于售价."""
        url = reverse("product-list")
        data = {
            "title": "测试",
            "price": 100,
            "original_price": 50,
            "category_id": str(category.id),
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── 商品列表 ──────────────────────────────────────────────
class TestProductList:
    def test_list_products(self, api_client, product, db):
        """获取商品列表应返回 200."""
        url = reverse("product-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_list_products_only_active(self, auth_client, user, category, db):
        """列表只显示在售商品（非卖家非管理员）."""
        Product.objects.create(
            seller=user, title="在售商品", price=10, status=Product.Status.ACTIVE
        )
        Product.objects.create(
            seller=user, title="已售商品", price=20, status=Product.Status.SOLD
        )
        Product.objects.create(
            seller=user, title="隐藏商品", price=30, status=Product.Status.HIDDEN
        )
        url = reverse("product-list")
        response = auth_client.get(url)
        data = response.data["data"]
        titles = [p["title"] for p in data]
        assert "在售商品" in titles
        assert "已售商品" not in titles
        assert "隐藏商品" not in titles

    def test_filter_by_category(self, api_client, product, category, db):
        """按分类筛选."""
        url = reverse("product-list") + f"?category={category.id}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_price_range(self, api_client, product, db):
        """按价格范围筛选."""
        url = reverse("product-list") + "?price_min=1000&price_max=3000"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1

    def test_search_products(self, api_client, product, db):
        """按标题搜索."""
        url = reverse("product-list") + "?search=笔记本"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1

    def test_sort_by_price_desc(self, api_client, user, db):
        """按价格降序排列."""
        Product.objects.create(seller=user, title="便宜", price=10, status=Product.Status.ACTIVE)
        Product.objects.create(seller=user, title="贵", price=1000, status=Product.Status.ACTIVE)
        url = reverse("product-list") + "?sort_by=price_desc"
        response = api_client.get(url)
        prices = [float(p["price"]) for p in response.data["data"]]
        assert prices == sorted(prices, reverse=True)


# ── 商品详情 ──────────────────────────────────────────────
class TestProductRetrieve:
    def test_get_product_detail(self, api_client, product, db):
        """获取商品详情应返回完整信息."""
        url = reverse("product-detail", kwargs={"id": product.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == product.title
        assert "description" in response.data["data"]

    def test_retrieve_increments_view_count(self, api_client, product, db):
        """浏览商品应自增浏览次数."""
        url = reverse("product-detail", kwargs={"id": product.id})
        old_count = product.view_count
        api_client.get(url)
        product.refresh_from_db()
        assert product.view_count == old_count + 1

    def test_get_product_not_found(self, api_client, db):
        """不存在的商品应返回 404."""
        url = reverse("product-detail", kwargs={"id": "00000000-0000-0000-0000-000000000000"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── 商品更新 ──────────────────────────────────────────────
class TestProductUpdate:
    def test_owner_can_update(self, auth_client, product, db):
        """卖家可以更新自己的商品."""
        url = reverse("product-detail", kwargs={"id": product.id})
        response = auth_client.patch(url, {"title": "新标题"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.title == "新标题"

    def test_non_owner_cannot_update(self, other_auth_client, product, db):
        """非卖家不能更新他人商品."""
        url = reverse("product-detail", kwargs={"id": product.id})
        response = other_auth_client.patch(url, {"title": "恶意修改"}, format="json")
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# ── 商品删除 ──────────────────────────────────────────────
class TestProductDelete:
    def test_owner_can_delete(self, auth_client, product, db):
        """卖家可以删除自己的商品."""
        url = reverse("product-detail", kwargs={"id": product.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_non_owner_cannot_delete(self, other_auth_client, product, db):
        """非卖家不能删除他人商品."""
        url = reverse("product-detail", kwargs={"id": product.id})
        response = other_auth_client.delete(url)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# ── 商品状态转换 ──────────────────────────────────────────
class TestProductStatusTransitions:
    def test_mark_reserved(self, auth_client, product, db):
        """卖家可标记已预定."""
        url = reverse("product-mark-reserved", kwargs={"id": product.id})
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.status == Product.Status.RESERVED

    def test_mark_sold(self, auth_client, product, db):
        """卖家可标记已售出."""
        url = reverse("product-mark-sold", kwargs={"id": product.id})
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.status == Product.Status.SOLD

    def test_mark_active(self, auth_client, product, db):
        """卖家可重新上架."""
        product.status = Product.Status.RESERVED
        product.save()
        url = reverse("product-mark-active", kwargs={"id": product.id})
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.status == Product.Status.ACTIVE

    def test_non_owner_cannot_change_status(self, other_auth_client, product, db):
        """非卖家不能修改商品状态."""
        url = reverse("product-mark-reserved", kwargs={"id": product.id})
        response = other_auth_client.post(url)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# ── 我的商品 ──────────────────────────────────────────────
class TestMyProducts:
    def test_my_products(self, auth_client, product, db):
        """获取我的商品列表."""
        url = reverse("product-my")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1

    def test_my_products_unauthenticated(self, api_client, db):
        """未登录不能查看我的商品."""
        url = reverse("product-my")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── 分类 API ──────────────────────────────────────────────
class TestCategoryAPI:
    def test_list_categories(self, api_client, category, db):
        """获取分类列表."""
        url = reverse("category-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1

    def test_retrieve_category(self, api_client, category, db):
        """获取分类详情."""
        url = reverse("category-detail", kwargs={"id": category.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["name"] == "电子产品"


# ── 标签 API ──────────────────────────────────────────────
class TestTagAPI:
    def test_list_tags(self, api_client, tag, db):
        """获取标签列表."""
        url = reverse("tag-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1
