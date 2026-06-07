"""SwapCampus 根路由配置."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import SimpleRouter

from apps.users.views import NotificationViewSet

notification_router = SimpleRouter()
notification_router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # API 文档
    path("api/docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # 业务 API
    path("api/users/", include("apps.users.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/transactions/", include("apps.transactions.urls")),
    path("api/chat/", include("apps.chat.urls")),
    path("api/admin/", include("apps.admin_panel.urls")),
    path("api/", include(notification_router.urls)),
]

# 开发环境：暴露媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
