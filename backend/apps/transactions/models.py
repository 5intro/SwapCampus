"""交易模块模型（占位，后端 B 实现）.

包含最小 Order 模型定义，供 users.CreditRecord 外键引用。
后端 B 需在此基础上扩展字段和完善交易模块逻辑。
"""

from django.db import models

from core.models import BaseModel


class Order(BaseModel):
    """订单模型（占位）.

    后端 B 需添加：buyer, seller, product, status, face_confirm 等字段。
    """

    # 占位字段，确保模型至少有一个非 id 字段
    status = models.CharField(
        max_length=20,
        default="pending",
        verbose_name="订单状态（占位）",
    )

    class Meta:
        db_table = "orders"
        verbose_name = "订单"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"Order {self.id}"
