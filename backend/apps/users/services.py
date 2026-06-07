"""用户业务逻辑.

- 信用分计算：根据交易行为规则增减信用分
- 积分记录创建：确保积分变更原子化并记录审计日志
"""

from django.db import transaction
from django.db.models import F

from apps.users.models import CreditRecord, User


# ── 信用分规则常量 ─────────────────────────────────────────
CREDIT_RULES = {
    "order_complete": +5,      # 成功完成一笔交易
    "good_review": +3,         # 获得一次好评
    "bad_review": -10,         # 获得一次差评
    "cancel_order": -2,        # 取消订单（买方/卖方）
    "violation": -20,          # 违规处罚
    "appeal_restore": +20,     # 申诉恢复
    "initial": 0,              # 初始积分（仅记录）
}


@transaction.atomic
def add_credit_record(
    user: User,
    change: int,
    reason: str,
    description: str = "",
    related_order=None,
) -> CreditRecord:
    """原子化地添加积分变更记录并更新用户信用分.

    使用 select_for_update 加行锁，防止并发积分覆盖问题。

    Args:
        user: 目标用户
        change: 积分变化量（正数加分，负数减分）
        reason: 变更原因（CreditRecord.ChangeReason 的 value）
        description: 详细说明
        related_order: 关联订单（可选）

    Returns:
        新创建的 CreditRecord 实例
    """
    # 锁定用户行，计算新积分（在同一行锁内读写，避免并发覆盖）
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    new_score = locked_user.credit_score + change
    if new_score < 0:
        new_score = 0
    locked_user.credit_score = new_score
    locked_user.save(update_fields=["credit_score"])

    record = CreditRecord.objects.create(
        user=user,
        change=change,
        reason=reason,
        description=description,
        score_after=new_score,
        related_order=related_order,
    )
    # 创建积分变动通知
    sign = "+" if change >= 0 else ""
    create_notification(
        user, "credit_change",
        "积分变动",
        f"你的信用分 {sign}{change}，当前 {new_score} 分",
        related_order=related_order,
    )
    return record


def create_notification(
    recipient,
    ntype: str,
    title: str,
    content: str = "",
    related_order=None,
    related_product=None,
):
    """创建站内通知."""
    from apps.users.models import Notification

    return Notification.objects.create(
        recipient=recipient,
        type=ntype,
        title=title,
        content=content,
        related_order=related_order,
        related_product=related_product,
    )


def get_credit_change(reason: str) -> int:
    """获取指定行为对应的信用分变化值.

    Args:
        reason: 行为原因（CREDIT_RULES 的 key）

    Returns:
        信用分变化值
    """
    return CREDIT_RULES.get(reason, 0)
