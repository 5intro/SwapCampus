"""管理面板 API 视图."""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product
from apps.transactions.models import Order
from core.utils import build_success_response

User = get_user_model()


class DashboardView(APIView):
    """管理仪表盘数据.

    GET /api/admin/dashboard/

    仅管理员可访问。
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="管理仪表盘",
        description="返回平台核心统计数据（仅管理员）",
    )
    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {"success": False, "data": None, "error": {"code": "FORBIDDEN", "message": "仅管理员可访问"}},
                status=403,
            )

        total_users = User.objects.filter(is_active=True).count()
        active_products = Product.objects.filter(status=Product.Status.ACTIVE).count()
        pending_orders = Order.objects.filter(status=Order.Status.PENDING).count()
        completed_orders = Order.objects.filter(status=Order.Status.COMPLETED).count()

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
            "recent_registrations": recent_users_data,
        }
        return Response(build_success_response(data))
