"""M4 交易模块单元测试.

测试覆盖：
- 订单创建
- 订单状态机
- 面交确认
- 评价
- 信用分联动
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.products.models import Product
from rest_framework.test import APIClient

from apps.transactions.models import Order, Review
from apps.transactions.services import create_face_confirm, create_review, transition_order, verify_face_confirm

User = get_user_model()


# ── 订单创建 ──────────────────────────────────────────────
class TestOrderCreate:
    def test_create_order_success(self, buyer_client, product, db):
        """买家可以创建订单."""
        url = reverse("order-list")
        data = {
            "product_id": str(product.id),
            "meet_time": "2026-06-10T12:00:00Z",
            "meet_location": "图书馆门口",
        }
        response = buyer_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

        # 商品应变为已预定
        product.refresh_from_db()
        assert product.status == Product.Status.RESERVED

    def test_create_order_own_product(self, seller_client, product, db):
        """不能购买自己的商品."""
        url = reverse("order-list")
        response = seller_client.post(
            url, {"product_id": str(product.id)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_inactive_product(self, buyer_client, product, db):
        """不能购买已售出商品."""
        product.status = Product.Status.SOLD
        product.save()
        url = reverse("order-list")
        response = buyer_client.post(
            url, {"product_id": str(product.id)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_duplicate_pending_order(self, buyer_client, product, buyer, seller, db):
        """同一买家对同一商品不能有重复进行中订单."""
        Order.objects.create(
            buyer=buyer, seller=seller, product=product, status=Order.Status.PENDING
        )
        url = reverse("order-list")
        response = buyer_client.post(
            url, {"product_id": str(product.id)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_cannot_create(self, api_client, product, db):
        """未登录不能创建订单."""
        url = reverse("order-list")
        response = api_client.post(url, {"product_id": str(product.id)}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── 订单状态机 ────────────────────────────────────────────
class TestOrderStateMachine:
    def test_seller_accept_order(self, seller_client, order, db):
        """卖家可以接受订单."""
        url = reverse("order-accept", kwargs={"id": order.id})
        response = seller_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == Order.Status.ACCEPTED

    def test_buyer_cannot_accept(self, buyer_client, order, db):
        """买家不能接受订单."""
        url = reverse("order-accept", kwargs={"id": order.id})
        response = buyer_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_seller_reject_order(self, seller_client, order, db):
        """卖家可以拒绝订单."""
        url = reverse("order-reject", kwargs={"id": order.id})
        response = seller_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == Order.Status.REJECTED

    def test_buyer_cancel_order(self, buyer_client, order, db):
        """买家可以取消订单."""
        url = reverse("order-cancel", kwargs={"id": order.id})
        response = buyer_client.post(url, {"cancel_reason": "不想要了"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == Order.Status.CANCELLED
        assert order.cancel_by_id == order.buyer_id

    def test_cancel_restores_product(self, buyer_client, buyer, seller, product, db):
        """取消订单应恢复商品状态."""
        order = Order.objects.create(
            buyer=buyer, seller=seller, product=product, status=Order.Status.PENDING
        )
        product.status = Product.Status.RESERVED
        product.save()
        url = reverse("order-cancel", kwargs={"id": order.id})
        buyer_client.post(url, {"cancel_reason": "test"}, format="json")
        product.refresh_from_db()
        assert product.status == Product.Status.ACTIVE

    def test_invalid_transition_completed_to_cancel(self, buyer_client, buyer, seller, product, db):
        """已完成订单不能再次取消（返回 400）."""
        order = Order.objects.create(
            buyer=buyer, seller=seller, product=product, status=Order.Status.COMPLETED
        )
        url = reverse("order-cancel", kwargs={"id": order.id})
        response = buyer_client.post(url, {"cancel_reason": "test"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_third_party_cannot_access(self, order, db):
        """第三方不能访问订单（返回 404 因为 queryset 已过滤）."""
        User.objects.create_user(username="20210003", password="TestPass123!")
        client = APIClient()
        url = reverse("token-obtain-pair")
        resp = client.post(url, {"username": "20210003", "password": "TestPass123!"})
        token = resp.data["data"]["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("order-detail", kwargs={"id": order.id})
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── 面交确认 ──────────────────────────────────────────────
class TestFaceConfirm:
    @pytest.fixture
    def accepted_order(self, buyer, seller, product, db):
        order = Order.objects.create(
            buyer=buyer,
            seller=seller,
            product=product,
            status=Order.Status.ACCEPTED,
        )
        return order

    def test_create_face_confirm(self, seller_client, accepted_order, db):
        """卖家可以生成面交确认码."""
        url = reverse("order-face-confirm", kwargs={"id": accepted_order.id})
        response = seller_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "confirm_code" in response.data["data"]
        accepted_order.refresh_from_db()
        assert accepted_order.status == Order.Status.FACE_CONFIRM

    def test_verify_face_confirm(self, seller_client, buyer_client, accepted_order, db):
        """买家验证确认码后订单完成."""
        # 卖家生成确认码
        url = reverse("order-face-confirm", kwargs={"id": accepted_order.id})
        gen_resp = seller_client.get(url)
        code = gen_resp.data["data"]["confirm_code"]

        # 买家验证
        response = buyer_client.post(url, {"code": code}, format="json")
        assert response.status_code == status.HTTP_200_OK
        accepted_order.refresh_from_db()
        assert accepted_order.status == Order.Status.COMPLETED

    def test_verify_wrong_code(self, seller_client, buyer_client, accepted_order, db):
        """错误确认码应返回 400."""
        url = reverse("order-face-confirm", kwargs={"id": accepted_order.id})
        gen_resp = seller_client.get(url)
        assert gen_resp.status_code == status.HTTP_200_OK

        response = buyer_client.post(url, {"code": "000000"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_buyer_cannot_generate_code(self, buyer_client, accepted_order, db):
        """买家不能生成确认码."""
        url = reverse("order-face-confirm", kwargs={"id": accepted_order.id})
        response = buyer_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── 评价 ──────────────────────────────────────────────────
class TestReview:
    @pytest.fixture
    def completed_order(self, buyer, seller, product, db):
        return Order.objects.create(
            buyer=buyer,
            seller=seller,
            product=product,
            status=Order.Status.COMPLETED,
        )

    def test_create_review_buyer_to_seller(self, buyer_client, completed_order, db):
        """买家完成交易后评价卖家."""
        url = reverse("review-list")
        data = {
            "order_id": str(completed_order.id),
            "rating": 5,
            "content": "卖家很靠谱",
        }
        response = buyer_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        completed_order.refresh_from_db()
        assert completed_order.buyer_rated is True

    def test_create_review_seller_to_buyer(self, seller_client, completed_order, db):
        """卖家完成交易后评价买家."""
        url = reverse("review-list")
        data = {
            "order_id": str(completed_order.id),
            "rating": 4,
            "content": "买家爽快",
        }
        response = seller_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        completed_order.refresh_from_db()
        assert completed_order.seller_rated is True

    def test_duplicate_review(self, buyer_client, completed_order, db):
        """同一个人不能重复评价同一订单."""
        url = reverse("review-list")
        data = {"order_id": str(completed_order.id), "rating": 5}
        buyer_client.post(url, data, format="json")
        response = buyer_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_review_pending_order(self, buyer_client, order, db):
        """不能评价未完成订单."""
        url = reverse("review-list")
        data = {"order_id": str(order.id), "rating": 5}
        response = buyer_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reviews_for_user(self, seller_client, completed_order, buyer, db):
        """获取用户的评价列表."""
        create_review(completed_order, buyer, 5, "好评")
        url = reverse("review-list") + f"?reviewee={completed_order.seller_id}"
        response = seller_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1


# ── 信用分联动 ────────────────────────────────────────────
class TestCreditIntegration:
    @pytest.fixture
    def completed_order(self, buyer, seller, product, db):
        order = Order.objects.create(
            buyer=buyer,
            seller=seller,
            product=product,
            status=Order.Status.PENDING,
        )
        transition_order(order, Order.Status.ACCEPTED, seller)
        return order

    def test_complete_order_credits(self, buyer_client, seller_client, completed_order, buyer, seller, db):
        """完成交易买卖双方各 +5 分."""
        old_buyer_score = buyer.credit_score
        old_seller_score = seller.credit_score

        # 面交确认完成
        url = reverse("order-face-confirm", kwargs={"id": completed_order.id})
        gen_resp = seller_client.get(url)
        code = gen_resp.data["data"]["confirm_code"]
        buyer_client.post(url, {"code": code}, format="json")

        buyer.refresh_from_db()
        seller.refresh_from_db()
        assert buyer.credit_score == old_buyer_score + 5
        assert seller.credit_score == old_seller_score + 5

    def test_cancel_order_penalty(self, buyer_client, buyer, seller, product, db):
        """取消订单扣 2 分."""
        order = Order.objects.create(
            buyer=buyer, seller=seller, product=product, status=Order.Status.PENDING
        )
        old_score = buyer.credit_score
        url = reverse("order-cancel", kwargs={"id": order.id})
        buyer_client.post(url, {"cancel_reason": "不想要了"}, format="json")
        buyer.refresh_from_db()
        assert buyer.credit_score == old_score - 2

    def test_good_review_bonus(self, buyer, seller, product, db):
        """好评 +3 分."""
        order = Order.objects.create(
            buyer=buyer, seller=seller, product=product, status=Order.Status.COMPLETED
        )
        old_score = seller.credit_score
        create_review(order, buyer, 5, "很好")
        seller.refresh_from_db()
        assert seller.credit_score == old_score + 3

    def test_bad_review_penalty(self, buyer, seller, product, db):
        """差评 -10 分."""
        order = Order.objects.create(
            buyer=buyer, seller=seller, product=product, status=Order.Status.COMPLETED
        )
        old_score = seller.credit_score
        create_review(order, buyer, 1, "很差")
        seller.refresh_from_db()
        assert seller.credit_score == old_score - 10
