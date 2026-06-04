"""交易模块业务逻辑 — 订单状态机、评价、面交确认."""

import random
from datetime import datetime

from django.db import transaction as db_transaction
from django.utils import timezone

from apps.products.models import Product
from apps.transactions.models import FaceConfirm, Order, Review

# ── 状态转换规则 ───────────────────────────────────────────
# pending 可以转换到的状态
ORDER_TRANSITIONS = {
    Order.Status.PENDING: [
        Order.Status.ACCEPTED,
        Order.Status.REJECTED,
        Order.Status.CANCELLED,
    ],
    Order.Status.ACCEPTED: [
        Order.Status.FACE_CONFIRM,
        Order.Status.CANCELLED,
    ],
    Order.Status.FACE_CONFIRM: [
        Order.Status.COMPLETED,
    ],
}

TERMINAL_STATUSES = {
    Order.Status.REJECTED,
    Order.Status.CANCELLED,
    Order.Status.COMPLETED,
}


def _get_credit_change(reason: str) -> int:
    """获取信用分变化值（避免循环导入）."""
    from apps.users.services import CREDIT_RULES
    return CREDIT_RULES.get(reason, 0)


def _add_credit(user, reason: str, description: str = "", related_order: Order | None = None):
    """原子化积分变更."""
    from apps.users.services import add_credit_record

    change = _get_credit_change(reason)
    if change != 0:
        add_credit_record(
            user=user,
            change=change,
            reason=reason,
            description=description,
            related_order=related_order,
        )


@db_transaction.atomic
def transition_order(order: Order, new_status_str: str, user, **kwargs) -> Order:
    """订单状态转换.

    Args:
        order: 订单实例
        new_status_str: 目标状态 (e.g. "accepted", "cancelled")
        user: 执行操作的用户
        **kwargs: 额外字段 (cancel_reason, meet_time 等)

    Returns:
        更新后的 Order 实例

    Raises:
        ValueError: 非法状态转换
    """
    current_status = order.status
    allowed = ORDER_TRANSITIONS.get(current_status, [])

    if new_status_str not in allowed:
        raise ValueError(
            f"不允许从 {current_status} 转换到 {new_status_str}。"
            f"允许的状态: {allowed}"
        )

    # 锁定订单行
    order = Order.objects.select_for_update().get(pk=order.pk)

    old_status = order.status
    order.status = new_status_str

    # 更新额外字段
    for field, value in kwargs.items():
        if hasattr(order, field):
            setattr(order, field, value)

    # ── 触发副作用 ──────────────────────────────────────
    if new_status_str == Order.Status.CANCELLED:
        order.cancel_by = user
        # 恢复商品状态
        Product.objects.filter(pk=order.product_id).update(
            status=Product.Status.ACTIVE
        )
        # 取消方扣 2 分
        _add_credit(user, "cancel_order", f"取消订单 #{order.id.hex[:8]}", order)

    elif new_status_str == Order.Status.COMPLETED:
        order.completed_at = timezone.now()
        # 买卖双方各 +5 分
        _add_credit(order.buyer, "order_complete", f"完成交易 #{order.id.hex[:8]}", order)
        _add_credit(order.seller, "order_complete", f"完成交易 #{order.id.hex[:8]}", order)
        # 商品标记为已售
        Product.objects.filter(pk=order.product_id).update(
            status=Product.Status.SOLD
        )

    order.save()
    return order


@db_transaction.atomic
def create_review(order: Order, reviewer, rating: int, content: str = "") -> Review:
    """创建交易评价.

    Args:
        order: 已完成的订单
        reviewer: 评价人
        rating: 评分 (1-5)
        content: 评价内容

    Returns:
        新创建的 Review 实例
    """
    if order.status != Order.Status.COMPLETED:
        raise ValueError("只能评价已完成的订单")

    if reviewer.id not in (order.buyer_id, order.seller_id):
        raise ValueError("只有买卖双方可以评价")

    # 确定评价类型和被评价人
    if reviewer.id == order.buyer_id:
        review_type = Review.ReviewType.BUYER_TO_SELLER
        reviewee = order.seller
        rated_flag = "buyer_rated"
    else:
        review_type = Review.ReviewType.SELLER_TO_BUYER
        reviewee = order.buyer
        rated_flag = "seller_rated"

    # 检查是否已评价
    if getattr(order, rated_flag):
        raise ValueError("您已经对此订单进行过评价")

    review = Review.objects.create(
        order=order,
        reviewer=reviewer,
        reviewee=reviewee,
        rating=rating,
        content=content,
        review_type=review_type,
    )

    # 更新订单的评价标记
    setattr(order, rated_flag, True)
    order.save(update_fields=[rated_flag, "updated_at"])

    # 信用分变动
    if rating >= 4:
        _add_credit(reviewee, "good_review", f"获得好评 (订单 #{order.id.hex[:8]})", order)
    elif rating <= 2:
        _add_credit(reviewee, "bad_review", f"获得差评 (订单 #{order.id.hex[:8]})", order)

    return review


def generate_face_confirm_code() -> str:
    """生成 6 位随机数字确认码."""
    return str(random.randint(100000, 999999))


@db_transaction.atomic
def create_face_confirm(order: Order, created_by) -> FaceConfirm:
    """生成面交确认码（卖家操作）."""
    if order.status != Order.Status.ACCEPTED:
        raise ValueError("只能在已接受状态下生成面交确认码")
    if created_by.id != order.seller_id:
        raise ValueError("只有卖家可以生成面交确认码")

    # 如果已有未过期的确认码，复用
    existing = FaceConfirm.objects.filter(
        order=order, status=FaceConfirm.Status.PENDING
    ).first()
    if existing:
        return existing

    code = generate_face_confirm_code()
    face_confirm = FaceConfirm.objects.create(
        order=order,
        confirm_code=code,
        created_by=created_by,
    )

    # 订单进入面交确认状态
    order.status = Order.Status.FACE_CONFIRM
    order.save(update_fields=["status", "updated_at"])

    return face_confirm


@db_transaction.atomic
def verify_face_confirm(order: Order, code: str, confirmed_by) -> Order:
    """验证面交确认码（买家操作）."""
    if order.status != Order.Status.FACE_CONFIRM:
        raise ValueError("订单不在面交确认状态")

    if confirmed_by.id != order.buyer_id:
        raise ValueError("只有买家可以验证确认码")

    try:
        face_confirm = FaceConfirm.objects.select_for_update().get(
            order=order, status=FaceConfirm.Status.PENDING
        )
    except FaceConfirm.DoesNotExist:
        raise ValueError("没有待确认的面交记录")

    if face_confirm.confirm_code != code:
        raise ValueError("确认码错误")

    face_confirm.status = FaceConfirm.Status.CONFIRMED
    face_confirm.confirmed_by = confirmed_by
    face_confirm.confirmed_at = timezone.now()
    face_confirm.save()

    # 订单完成
    return transition_order(
        order,
        Order.Status.COMPLETED,
        confirmed_by,
    )
