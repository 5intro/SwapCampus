"""M1 用户体系单元测试.

测试覆盖：
- 用户注册
- 用户登录（JWT）
- 用户列表/详情获取
- 用户信息更新
- 信用分变更逻辑
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import CreditRecord
from apps.users.services import add_credit_record

User = get_user_model()


# ── Fixtures ───────────────────────────────────────────────
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        "username": "20210001",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
        "email": "test@bjfu.edu.cn",
        "nickname": "测试用户",
        "campus": "校本部",
    }


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="20210001",
        password="TestPass123!",
        nickname="测试用户",
    )


@pytest.fixture
def auth_client(api_client, user):
    """已认证的 API 客户端."""
    url = reverse("token-obtain-pair")
    response = api_client.post(
        url, {"username": "20210001", "password": "TestPass123!"}
    )
    token = response.data["data"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ── 注册测试 ──────────────────────────────────────────────
class TestRegister:
    def test_register_success(self, api_client, user_data, db):
        """正常注册应返回 201 和用户数据."""
        url = reverse("user-register")
        response = api_client.post(url, user_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        data = response.data["data"]
        assert data["username"] == "20210001"
        assert "password" not in data

    def test_register_duplicate_student_id(self, api_client, user_data, db):
        """重复学号注册应返回 400."""
        url = reverse("user-register")
        api_client.post(url, user_data)
        response = api_client.post(url, user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client, user_data, db):
        """两次密码不一致应返回 400."""
        url = reverse("user-register")
        user_data["password_confirm"] = "DifferentPass1!"
        response = api_client.post(url, user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── 登录测试 ──────────────────────────────────────────────
class TestLogin:
    def test_login_success(self, api_client, user, db):
        """正确凭证登录应返回 access + refresh token."""
        url = reverse("token-obtain-pair")
        response = api_client.post(
            url, {"username": "20210001", "password": "TestPass123!"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["data"]
        assert "refresh" in response.data["data"]

    def test_login_wrong_password(self, api_client, user, db):
        """错误密码应返回 401."""
        url = reverse("token-obtain-pair")
        response = api_client.post(
            url, {"username": "20210001", "password": "WrongPass1!"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self, api_client, user, db):
        """刷新 token 应返回新 access token."""
        # 先获取 token
        login_url = reverse("token-obtain-pair")
        login_resp = api_client.post(
            login_url, {"username": "20210001", "password": "TestPass123!"}
        )
        refresh = login_resp.data["data"]["refresh"]

        # 刷新
        refresh_url = reverse("token-refresh")
        response = api_client.post(refresh_url, {"refresh": refresh})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data["data"]


# ── 用户信息测试 ──────────────────────────────────────────
class TestUserProfile:
    def test_get_user_list(self, auth_client, user):
        """获取用户列表应返回 200."""
        url = reverse("user-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_get_user_detail(self, auth_client, user):
        """获取用户详情应返回公开信息，不含 email."""
        url = reverse("user-detail", kwargs={"id": user.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["username"] == "20210001"
        assert "email" not in data  # 公开信息不暴露 email

    def test_get_me(self, auth_client, user):
        """获取当前用户信息应包含 email."""
        url = reverse("user-me")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert "email" in data

    def test_update_me(self, auth_client, user):
        """更新当前用户信息应成功."""
        url = reverse("user-me")
        response = auth_client.patch(
            url,
            {"nickname": "新昵称", "bio": "这是我的简介"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.nickname == "新昵称"
        assert user.bio == "这是我的简介"

    def test_unauthenticated_access(self, api_client, user):
        """未登录用户应能获取公开列表但无法获取 me."""
        list_url = reverse("user-list")
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK

        me_url = reverse("user-me")
        response = api_client.get(me_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── 信用分测试 ────────────────────────────────────────────
class TestCreditService:
    def test_add_credit_record(self, user, db):
        """添加积分记录应更新用户积分."""
        record = add_credit_record(
            user=user,
            change=5,
            reason="order_complete",
            description="完成交易 #123",
        )
        user.refresh_from_db()
        assert record.score_after == 105
        assert user.credit_score == 105

    def test_credit_score_not_negative(self, user, db):
        """信用分不应变为负数."""
        user.credit_score = 3
        user.save()
        record = add_credit_record(
            user=user,
            change=-10,
            reason="bad_review",
            description="差评",
        )
        user.refresh_from_db()
        assert record.score_after == 0
        assert user.credit_score == 0

    def test_credit_level_property(self, user, db):
        """信用等级应正确计算."""
        user.credit_score = 160
        assert user.credit_level == "excellent"
        user.credit_score = 120
        assert user.credit_level == "good"
        user.credit_score = 80
        assert user.credit_level == "fair"
        user.credit_score = 40
        assert user.credit_level == "poor"


class TestCreditRecordsAPI:
    def test_get_own_credit_records(self, auth_client, user, db):
        """查看自己的积分记录应成功."""
        CreditRecord.objects.create(
            user=user,
            change=5,
            reason="order_complete",
            score_after=105,
        )
        url = reverse("user-credit-records", kwargs={"id": user.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 1

    def test_cannot_see_others_private_records(self, auth_client, user, db):
        """不能查看他人的非公开积分记录."""
        other = User.objects.create_user(username="20210002", password="pass")
        CreditRecord.objects.create(
            user=other,
            change=-20,
            reason="violation",
            score_after=80,
        )
        url = reverse("user-credit-records", kwargs={"id": other.id})
        response = auth_client.get(url)
        # 违规记录不公开，不应返回
        assert len(response.data["data"]) == 0
