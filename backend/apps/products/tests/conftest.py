"""Products 模块 test fixtures."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.products.models import Category, Product, ProductImage, Tag

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="20210001",
        password="TestPass123!",
        nickname="卖家用户",
        verification_status="approved",
    )


@pytest.fixture
def auth_client(api_client, user):
    url = reverse("token-obtain-pair")
    response = api_client.post(url, {"username": "20210001", "password": "TestPass123!"})
    token = response.data["data"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="20210002",
        password="TestPass123!",
        nickname="其他用户",
    )


@pytest.fixture
def other_auth_client(api_client, other_user):
    url = reverse("token-obtain-pair")
    response = api_client.post(url, {"username": "20210002", "password": "TestPass123!"})
    token = response.data["data"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def category(db):
    return Category.objects.create(name="电子产品", icon="📱", sort_order=1)


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="九成新")


@pytest.fixture
def product(user, category, tag, db):
    p = Product.objects.create(
        seller=user,
        title="二手笔记本电脑",
        description="功能正常，电池健康度 85%",
        price=2500.00,
        original_price=5999.00,
        condition=Product.Condition.LIKE_NEW,
        status=Product.Status.ACTIVE,
        category=category,
        campus="校本部",
    )
    p.tags.add(tag)
    return p
