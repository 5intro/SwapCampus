"""管理面板 API 视图."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product, Report
from apps.transactions.models import Order
from core.utils import build_success_response

User = get_user_model()


def _require_admin(user):
    """检查用户是否为管理员，返回 None 或 403 Response."""
    if not user.is_staff:
        return Response(
            {
                "success": False,
                "data": None,
                "error": {"code": "FORBIDDEN", "message": "仅管理员可访问"},
            },
            status=403,
        )
    return None


class AdminPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ═══════════════════════════════════════════════════════════
# 管理仪表盘
# ═══════════════════════════════════════════════════════════
class DashboardView(APIView):
    """管理仪表盘数据.

    GET /api/admin/dashboard/
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="管理仪表盘",
        description="返回平台核心统计数据（仅管理员）",
    )
    def get(self, request):
        err = _require_admin(request.user)
        if err:
            return err

        total_users = User.objects.filter(is_active=True).count()
        active_products = Product.objects.filter(status=Product.Status.ACTIVE).count()
        pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
        completed_orders = Order.objects.filter(status=Order.Status.COMPLETED).count()
        pending_reports = Report.objects.filter(status=Report.Status.PENDING).count()

        recent_users = User.objects.filter(is_active=True).order_by("-date_joined")[:5]
        recent_users_data = [
            {
                "id": str(u.id),
                "username": u.username,
                "nickname": u.get_display_name(),
                "date_joined": u.date_joined,
            }
            for u in recent_users
        ]

        data = {
            "total_users": total_users,
            "active_products": active_products,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "pending_reports": pending_reports,
            "recent_registrations": recent_users_data,
        }
        return Response(build_success_response(data))


# ═══════════════════════════════════════════════════════════
# 商品管理
# ═══════════════════════════════════════════════════════════
class AdminProductListView(APIView):
    """管理员商品列表.

    GET  /api/admin/products/        → 商品列表（支持筛选）
    POST /api/admin/products/{id}/approve/ → 审核通过
    POST /api/admin/products/{id}/hide/    → 隐藏商品
    POST /api/admin/products/{id}/delete/  → 删除商品
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        err = _require_admin(request.user)
        if err:
            return err

        status_filter = request.query_params.get("status")
        search = request.query_params.get("search", "")
        qs = Product.objects.select_related("seller", "category").order_by("-created_at")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request)
        data = [
            {
                "id": str(p.id),
                "title": p.title,
                "price": str(p.price),
                "status": p.status,
                "status_display": p.get_status_display(),
                "seller": {
                    "id": str(p.seller.id),
                    "username": p.seller.username,
                    "nickname": p.seller.get_display_name(),
                },
                "category": p.category.name if p.category else None,
                "created_at": p.created_at,
            }
            for p in page
        ]
        return Response(
            {
                "success": True,
                "data": data,
                "error": None,
                "pagination": {
                    "page": paginator.page.number,
                    "page_size": paginator.get_page_size(request),
                    "total": paginator.page.paginator.count,
                },
            }
        )

    def post(self, request, product_id, action):
        err = _require_admin(request.user)
        if err:
            return err

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "NOT_FOUND", "message": "商品不存在"},
                },
                status=404,
            )

        if action == "approve":
            product.status = Product.Status.ACTIVE
            product.save(update_fields=["status", "updated_at"])
            return Response(build_success_response({"status": "approved"}))
        elif action == "hide":
            product.status = Product.Status.HIDDEN
            product.save(update_fields=["status", "updated_at"])
            return Response(build_success_response({"status": "hidden"}))
        elif action == "delete":
            product.delete()
            return Response(build_success_response({"status": "deleted"}))
        else:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "INVALID_ACTION", "message": "无效操作"},
                },
                status=400,
            )


# ═══════════════════════════════════════════════════════════
# 举报处理
# ═══════════════════════════════════════════════════════════
class AdminReportListView(APIView):
    """管理员举报列表与处理.

    GET  /api/admin/reports/             → 举报列表
    POST /api/admin/reports/{id}/handle/ → 处理举报
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        err = _require_admin(request.user)
        if err:
            return err

        status_filter = request.query_params.get("status")
        qs = Report.objects.select_related("reporter", "product", "handled_by").order_by(
            "-created_at"
        )

        if status_filter:
            qs = qs.filter(status=status_filter)

        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request)
        data = [
            {
                "id": str(r.id),
                "reporter": {
                    "id": str(r.reporter.id),
                    "username": r.reporter.username,
                    "nickname": r.reporter.get_display_name(),
                },
                "product": {
                    "id": str(r.product.id),
                    "title": r.product.title,
                    "status": r.product.status,
                },
                "reason": r.reason,
                "reason_display": r.get_reason_display(),
                "description": r.description,
                "status": r.status,
                "status_display": r.get_status_display(),
                "handled_by": (
                    {"id": str(r.handled_by.id), "nickname": r.handled_by.get_display_name()}
                    if r.handled_by
                    else None
                ),
                "handled_note": r.handled_note,
                "created_at": r.created_at,
            }
            for r in page
        ]
        return Response(
            {
                "success": True,
                "data": data,
                "error": None,
                "pagination": {
                    "page": paginator.page.number,
                    "page_size": paginator.page_size,
                    "total": paginator.page.paginator.count,
                },
            }
        )

    def post(self, request, report_id):
        """处理举报：驳回或处理（可附带隐藏商品）."""
        err = _require_admin(request.user)
        if err:
            return err

        action = request.data.get("action")  # "resolve" or "dismiss"
        note = request.data.get("note", "")
        hide_product = request.data.get("hide_product", False)

        if action not in ("resolve", "dismiss"):
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "INVALID_ACTION", "message": "操作必须为 resolve 或 dismiss"},
                },
                status=400,
            )

        try:
            report = Report.objects.select_related("product").get(id=report_id)
        except Report.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "NOT_FOUND", "message": "举报不存在"},
                },
                status=404,
            )

        if report.status != Report.Status.PENDING:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "ALREADY_HANDLED", "message": "该举报已被处理"},
                },
                status=400,
            )

        report.status = (
            Report.Status.RESOLVED if action == "resolve" else Report.Status.DISMISSED
        )
        report.handled_by = request.user
        report.handled_note = note
        report.save(update_fields=["status", "handled_by", "handled_note"])

        # 如果选择隐藏商品，同时下架该商品
        product_action = None
        if hide_product:
            report.product.status = Product.Status.HIDDEN
            report.product.save(update_fields=["status", "updated_at"])
            product_action = "商品已下架"

        return Response(
            build_success_response(
                {
                    "report_status": report.get_status_display(),
                    "product_action": product_action,
                }
            )
        )


# ═══════════════════════════════════════════════════════════
# 用户管理
# ═══════════════════════════════════════════════════════════
class AdminUserListView(APIView):
    """管理员用户列表与管理.

    GET  /api/admin/users/           → 用户列表
    POST /api/admin/users/{id}/ban/  → 封禁/解封用户
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        err = _require_admin(request.user)
        if err:
            return err

        search = request.query_params.get("search", "")
        active_filter = request.query_params.get("is_active")
        qs = User.objects.order_by("-date_joined")

        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(nickname__icontains=search)
                | Q(email__icontains=search)
            )
        if active_filter is not None:
            qs = qs.filter(is_active=active_filter.lower() in ("true", "1", "yes"))

        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request)
        data = [
            {
                "id": str(u.id),
                "username": u.username,
                "nickname": u.get_display_name(),
                "email": u.email or "",
                "credit_score": u.credit_score,
                "credit_level": u.credit_level,
                "campus": u.campus,
                "is_active": u.is_active,
                "is_staff": u.is_staff,
                "date_joined": u.date_joined,
            }
            for u in page
        ]
        return Response(
            {
                "success": True,
                "data": data,
                "error": None,
                "pagination": {
                    "page": paginator.page.number,
                    "page_size": paginator.page_size,
                    "total": paginator.page.paginator.count,
                },
            }
        )

    def post(self, request, user_id):
        """封禁/解封用户."""
        err = _require_admin(request.user)
        if err:
            return err

        action = request.data.get("action")  # "ban" or "unban"
        if action not in ("ban", "unban"):
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "INVALID_ACTION", "message": "操作必须为 ban 或 unban"},
                },
                status=400,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "NOT_FOUND", "message": "用户不存在"},
                },
                status=404,
            )

        # 不允许封禁自己
        if user == request.user:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "CANNOT_BAN_SELF", "message": "不能封禁自己"},
                },
                status=400,
            )

        user.is_active = action == "unban"
        user.save(update_fields=["is_active"])
        return Response(
            build_success_response(
                {"status": "banned" if action == "ban" else "unbanned"}
            )
        )


# ═══════════════════════════════════════════════════════════
# 学生证认证审核
# ═══════════════════════════════════════════════════════════
class AdminVerificationListView(APIView):
    """管理员学生证认证审核列表.

    GET  /api/admin/verifications/              → 待审核列表
    POST /api/admin/verifications/{user_id}/review/ → 通过/拒绝
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        err = _require_admin(request.user)
        if err:
            return err

        status_filter = request.query_params.get("status", "pending")
        search = request.query_params.get("search", "")
        qs = User.objects.filter(verification_status__in=["pending", "approved", "rejected"])

        if status_filter:
            qs = qs.filter(verification_status=status_filter)
        if search:
            qs = qs.filter(
                Q(username__icontains=search) | Q(nickname__icontains=search)
            )

        qs = qs.order_by("-date_joined")

        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request)
        data = [
            {
                "id": str(u.id),
                "username": u.username,
                "nickname": u.get_display_name(),
                "avatar": request.build_absolute_uri(u.avatar.url) if u.avatar else None,
                "student_id_card": request.build_absolute_uri(u.student_id_card.url) if u.student_id_card else None,
                "verification_status": u.verification_status,
                "verification_status_display": u.get_verification_status_display(),
                "verification_note": u.verification_note,
                "date_joined": u.date_joined,
            }
            for u in page
        ]
        return Response(
            {
                "success": True,
                "data": data,
                "error": None,
                "pagination": {
                    "page": paginator.page.number,
                    "page_size": paginator.page_size,
                    "total": paginator.page.paginator.count,
                },
            }
        )

    def post(self, request, user_id):
        """审核学生证：通过或拒绝."""
        err = _require_admin(request.user)
        if err:
            return err

        action = request.data.get("action")  # "approve" or "reject"
        note = request.data.get("note", "")

        if action not in ("approve", "reject"):
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "INVALID_ACTION", "message": "操作必须为 approve 或 reject"},
                },
                status=400,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "NOT_FOUND", "message": "用户不存在"},
                },
                status=404,
            )

        if user.verification_status != User.VerificationStatus.PENDING:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {"code": "ALREADY_HANDLED", "message": "该认证已处理"},
                },
                status=400,
            )

        user.verification_status = (
            User.VerificationStatus.APPROVED if action == "approve" else User.VerificationStatus.REJECTED
        )
        user.verification_note = note
        user.save(update_fields=["verification_status", "verification_note"])
        return Response(
            build_success_response(
                {
                    "status": "approved" if action == "approve" else "rejected",
                    "note": note,
                }
            )
        )
