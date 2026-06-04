"""M6 管理面板单元测试."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin001",
        password="AdminPass123!",
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        username="20210001",
        password="TestPass123!",
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    url = reverse("token-obtain-pair")
    response = api_client.post(url, {"username": "admin001", "password": "AdminPass123!"})
    token = response.data["data"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def user_client(api_client, normal_user):
    url = reverse("token-obtain-pair")
    response = api_client.post(url, {"username": "20210001", "password": "TestPass123!"})
    token = response.data["data"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


class TestDashboardAPI:
    def test_admin_can_access_dashboard(self, admin_client, db):
        """管理员可访问仪表盘."""
        url = reverse("admin-dashboard")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        data = response.data["data"]
        assert "total_users" in data
        assert "active_products" in data
        assert "pending_orders" in data
        assert "completed_orders" in data
        assert "recent_registrations" in data

    def test_normal_user_cannot_access_dashboard(self, user_client, db):
        """普通用户不能访问仪表盘."""
        url = reverse("admin-dashboard")
        response = user_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_access_dashboard(self, api_client, db):
        """未登录不能访问仪表盘."""
        url = reverse("admin-dashboard")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_counts(self, admin_client, db):
        """验证仪表盘统计数据."""
        # 创建一些数据
        User.objects.create_user(username="20210002", password="pass")
        url = reverse("admin-dashboard")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        # admin + normal_user + new user = 3 active users
        assert data["total_users"] >= 2
