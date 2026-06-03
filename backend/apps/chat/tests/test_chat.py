"""M5 站内通讯单元测试.

测试覆盖：
- 会话创建与获取
- 消息发送与获取
- 消息已读标记
- WebSocket 连接鉴权（基础验证）
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.chat.models import Conversation, Message

User = get_user_model()


# ── Fixtures ───────────────────────────────────────────────
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        username="20210001", password="TestPass123!", nickname="用户A"
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        username="20210002", password="TestPass123!", nickname="用户B"
    )


@pytest.fixture
def auth_client_a(api_client, user_a):
    """已认证的客户端（用户 A）."""
    url = reverse("token-obtain-pair")
    response = api_client.post(
        url, {"username": "20210001", "password": "TestPass123!"}
    )
    token = response.data["data"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def auth_client_b(api_client, user_b):
    """已认证的客户端（用户 B）."""
    url = reverse("token-obtain-pair")
    response = api_client.post(
        url, {"username": "20210002", "password": "TestPass123!"}
    )
    token = response.data["data"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def conversation(db, user_a, user_b):
    """创建一个测试会话."""
    conv = Conversation.objects.create()
    conv.participants.add(user_a, user_b)
    return conv


# ── 会话测试 ──────────────────────────────────────────────
class TestConversation:
    def test_create_conversation(self, auth_client_a, user_b):
        """创建新会话应成功."""
        url = reverse("conversation-list")
        response = auth_client_a.post(
            url,
            {"participant_id": str(user_b.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True

    def test_create_duplicate_conversation_reuses(self, auth_client_a, user_b):
        """与同一用户重复创建会话应复用已有会话."""
        url = reverse("conversation-list")
        data = {"participant_id": str(user_b.id)}
        resp1 = auth_client_a.post(url, data, format="json")
        resp2 = auth_client_a.post(url, data, format="json")
        assert resp1.data["data"]["id"] == resp2.data["data"]["id"]

    def test_cannot_create_self_conversation(self, auth_client_a, user_a):
        """不能与自己创建会话."""
        url = reverse("conversation-list")
        response = auth_client_a.post(
            url,
            {"participant_id": str(user_a.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_conversations(self, auth_client_a, conversation):
        """获取会话列表应只返回本人参与的."""
        url = reverse("conversation-list")
        response = auth_client_a.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1

    def test_other_user_cannot_see_conversation(self, auth_client_a, user_a, user_b):
        """用户不应看到自己不参与的会话."""
        # 创建只有 user_b 参与的会话
        conv = Conversation.objects.create()
        conv.participants.add(user_b)
        url = reverse("conversation-list")
        response = auth_client_a.get(url)
        conv_ids = [c["id"] for c in response.data["data"]]
        assert str(conv.id) not in conv_ids

    def test_retrieve_conversation_detail(self, auth_client_a, conversation):
        """获取会话详情应成功."""
        url = reverse("conversation-detail", kwargs={"id": conversation.id})
        response = auth_client_a.get(url)
        assert response.status_code == status.HTTP_200_OK


# ── 消息测试 ──────────────────────────────────────────────
class TestMessage:
    def test_send_message(self, auth_client_a, conversation):
        """发送消息应成功."""
        url = reverse("conversation-list-messages", kwargs={"id": conversation.id})
        response = auth_client_a.post(
            url,
            {"content": "你好，请问这个还在吗？"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["content"] == "你好，请问这个还在吗？"

    def test_get_messages(self, auth_client_a, conversation):
        """获取消息列表应成功."""
        # 先发几条消息
        Message.objects.create(
            conversation=conversation,
            sender=conversation.participants.first(),
            content="消息1",
        )
        Message.objects.create(
            conversation=conversation,
            sender=conversation.participants.first(),
            content="消息2",
        )
        url = reverse("conversation-list-messages", kwargs={"id": conversation.id})
        response = auth_client_a.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 2

    def test_mark_read(self, auth_client_a, auth_client_b, user_a, user_b, conversation):
        """标记已读应成功更新未读消息."""
        # 用户 A 发送消息
        msg = Message.objects.create(
            conversation=conversation,
            sender=user_a,
            content="来自A的消息",
        )
        # 用户 B 标记已读
        url = reverse("conversation-mark-read", kwargs={"id": conversation.id})
        response = auth_client_b.post(url)
        assert response.status_code == status.HTTP_200_OK
        msg.refresh_from_db()
        assert msg.is_read is True

    def test_unauthorized_message_access(self, api_client, conversation):
        """未登录用户不能访问消息."""
        url = reverse("conversation-list-messages", kwargs={"id": conversation.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── 模型测试 ──────────────────────────────────────────────
class TestChatModels:
    def test_conversation_last_message(self, conversation, user_a):
        """last_message 属性应返回最新消息."""
        Message.objects.create(conversation=conversation, sender=user_a, content="旧消息")
        Message.objects.create(conversation=conversation, sender=user_a, content="新消息")
        assert conversation.last_message.content == "新消息"

    def test_conversation_get_title(self, conversation, user_a, user_b):
        """会话标题应显示对方昵称."""
        title = conversation.get_title_for_user(user_a)
        assert "用户B" in title

    def test_message_ordering(self, conversation, user_a):
        """消息应按时间正序排列."""
        m1 = Message.objects.create(conversation=conversation, sender=user_a, content="第一条")
        m2 = Message.objects.create(conversation=conversation, sender=user_a, content="第二条")
        messages = list(conversation.messages.all())
        assert messages[0].content == "第一条"
        assert messages[1].content == "第二条"
