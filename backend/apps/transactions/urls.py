"""交易模块 API 路由."""

from rest_framework.routers import SimpleRouter

from apps.transactions.views import OrderViewSet, ReviewViewSet

router = SimpleRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"reviews", ReviewViewSet, basename="review")

urlpatterns = router.urls
