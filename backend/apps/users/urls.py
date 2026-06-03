"""用户体系 API 路由."""

from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.users.views import RegisterView, TokenObtainPairView, TokenRefreshView, UserViewSet

router = SimpleRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    # 注册
    path("register/", RegisterView.as_view(), name="user-register"),
    # 登录（JWT）
    path("login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    # 刷新 Token
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]

urlpatterns += router.urls
