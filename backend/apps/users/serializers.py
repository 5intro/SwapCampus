"""用户体系序列化器."""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.users.models import CreditRecord

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# 注册
# ═══════════════════════════════════════════════════════════
class RegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器.

    学号作为 username，密码需符合 Django 密码验证策略。
    """

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "password_confirm",
            "email",
            "nickname",
            "campus",
        ]
        extra_kwargs = {
            "username": {
                "help_text": "北京林业大学学号（8-9 位数字）",
                "min_length": 8,
                "max_length": 9,
            },
            "email": {"required": False},
            "nickname": {"required": False},
            "campus": {"required": False},
        }

    def validate_username(self, value):
        """校验学号格式：8-9 位数字."""
        if not re.match(r"^\d{8,9}$", value):
            raise serializers.ValidationError("学号必须为 8-9 位数字")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("该学号已注册")
        return value

    def validate(self, attrs):
        """校验两次密码一致."""
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "两次密码输入不一致"})
        return attrs

    def create(self, validated_data):
        """使用 create_user 创建用户（密码自动哈希）."""
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ═══════════════════════════════════════════════════════════
# 用户信息
# ═══════════════════════════════════════════════════════════
class UserSerializer(serializers.ModelSerializer):
    """用户公开信息序列化器.

    供商品详情页展示卖家信息、聊天列表显示对话用户等场景使用。
    不暴露 email、手机号等隐私字段。
    """

    credit_level = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "nickname",
            "avatar",
            "credit_score",
            "credit_level",
            "campus",
            "bio",
            "date_joined",
        ]
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """用户个人信息序列化器（仅本人可查看/编辑）.

    包含 email 等隐私字段，用于个人主页展示。
    """

    credit_level = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "nickname",
            "avatar",
            "credit_score",
            "credit_level",
            "campus",
            "bio",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "username",
            "credit_score",
            "credit_level",
            "date_joined",
        ]

    def update(self, instance, validated_data):
        """更新用户信息，avatar 字段需要特殊处理."""
        # 如果 avatar 在数据中且是空字符串，视为清除头像
        if "avatar" in validated_data and (
            validated_data["avatar"] is None
            or validated_data["avatar"] == ""
        ):
            instance.avatar.delete(save=False)
            validated_data.pop("avatar", None)
        return super().update(instance, validated_data)


class UserUpdateSerializer(UserProfileSerializer):
    """用户信息更新序列化器（不包含任何只读字段）.

    专门处理 PATCH 请求，允许部分更新。
    """

    pass


# ═══════════════════════════════════════════════════════════
# 积分记录
# ═══════════════════════════════════════════════════════════
class CreditRecordSerializer(serializers.ModelSerializer):
    """信用积分记录序列化器."""

    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = CreditRecord
        fields = [
            "id",
            "user",
            "change",
            "reason",
            "reason_display",
            "description",
            "score_after",
            "related_order",
            "created_at",
        ]
        read_only_fields = fields
