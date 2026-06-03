"""商品模块模型（占位，后端 B 实现）.

包含最小 Product 模型定义，供 chat.Conversation 外键引用。
后端 B 需在此基础上扩展字段和完善商品模块逻辑。
"""

from django.db import models

from core.models import BaseModel


class Product(BaseModel):
    """商品模型（占位）.

    后端 B 需添加：title, description, price, category, images, status 等字段。
    """

    # 占位字段，确保模型至少有一个非 id 字段
    title = models.CharField(max_length=200, verbose_name="商品标题（占位）")

    class Meta:
        db_table = "products"
        verbose_name = "商品"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.title
