"""管理面板 API 路由."""

from django.urls import path

from apps.admin_panel.views import (
    AdminProductListView,
    AdminReportListView,
    AdminUserListView,
    AdminVerificationListView,
    DashboardView,
)

urlpatterns = [
    # 仪表盘
    path("dashboard/", DashboardView.as_view(), name="admin-dashboard"),
    # 商品管理
    path("products/", AdminProductListView.as_view(), name="admin-products"),
    path(
        "products/<uuid:product_id>/<str:action>/",
        AdminProductListView.as_view(),
        name="admin-product-action",
    ),
    # 举报处理
    path("reports/", AdminReportListView.as_view(), name="admin-reports"),
    path(
        "reports/<uuid:report_id>/handle/",
        AdminReportListView.as_view(),
        name="admin-report-handle",
    ),
    # 用户管理
    path("users/", AdminUserListView.as_view(), name="admin-users"),
    path(
        "users/<uuid:user_id>/manage/",
        AdminUserListView.as_view(),
        name="admin-user-manage",
    ),
    # 学生证认证审核
    path("verifications/", AdminVerificationListView.as_view(), name="admin-verifications"),
    path(
        "verifications/<uuid:user_id>/review/",
        AdminVerificationListView.as_view(),
        name="admin-verification-review",
    ),
]
