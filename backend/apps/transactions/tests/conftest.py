"""Transactions 模块 test fixtures."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.products.models import Product
from apps.transactions.models import Order

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def buyer(db):
    return User.objects.create_user(
        username="20210001",
        password="TestPass123!",
        nickname="买家用户",
    )


@pytest.fixture
def seller(db):
    return User.objects.create_user(
        username="20210002",
        password="TestPass123!",
        nickname="卖家用户",
    )


@pytest.fixture
def buyer_client(buyer):
    """独立的买家认证客户端."""
    client = APIClient()
    url = reverse("token-obtain-pair")
    response = client.post(url, {"username": "20210001", "password": "TestPass123!"})
    token = response.data["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def seller_client(seller):
    """独立的卖家认证客户端."""
    client = APIClient()
    url = reverse("token-obtain-pair")
    response = client.post(url, {"username": "20210002", "password": "TestPass123!"})
    token = response.data["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def product(seller, db):
    return Product.objects.create(
        seller=seller,
        title="二手测试商品",
        price=100.00,
        condition=Product.Condition.USED,
        status=Product.Status.ACTIVE,
    )


@pytest.fixture
def order(buyer, seller, product, db):
    return Order.objects.create(
        buyer=buyer,
        seller=seller,
        product=product,
        status=Order.Status.PENDING,
    )
