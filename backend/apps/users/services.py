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
    # 锁定用户行，计算新积分
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    new_score = locked_user.credit_score + change
    # 积分下限 0（信用分不会变为负数）
    if new_score < 0:
        new_score = 0

    # 同时更新用户积分和创建记录
    User.objects.filter(pk=user.pk).update(credit_score=new_score)
    record = CreditRecord.objects.create(
        user=user,
        change=change,
        reason=reason,
        description=description,
        score_after=new_score,
        related_order=related_order,
    )
    return record


def get_credit_change(reason: str) -> int:
    """获取指定行为对应的信用分变化值.

    Args:
        reason: 行为原因（CREDIT_RULES 的 key）

    Returns:
        信用分变化值
    """
    return CREDIT_RULES.get(reason, 0)
