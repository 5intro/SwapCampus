"""管理面板 API 路由."""

from django.urls import path

from apps.admin_panel.views import DashboardView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="admin-dashboard"),
]
