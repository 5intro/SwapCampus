"""共享基础模型.

BaseModel 为所有业务模型提供统一字段：
- uuid（主键，对外暴露 ID，避免自增 ID 被遍历）
- created_at（创建时间）
- updated_at（修改时间）
"""

import uuid

from django.db import models


class BaseModel(models.Model):
    """所有业务模型的抽象基类.

    使用 UUID 作为主键，避免在 API 中暴露自增 ID 带来的安全隐患，
    同时保留 created_at / updated_at 用于审计追踪。
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="主键",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="修改时间",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
