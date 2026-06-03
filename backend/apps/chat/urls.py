"""站内通讯 REST API 路由."""

from rest_framework.routers import SimpleRouter

from apps.chat.views import ConversationViewSet

router = SimpleRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")

urlpatterns = router.urls
