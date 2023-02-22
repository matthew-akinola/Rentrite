from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AttachmentViewSet, ConversationViewSet, MessageViewSet

router = DefaultRouter()


router.register("conversations", ConversationViewSet)
router.register("messages", MessageViewSet)
router.register("attachment", AttachmentViewSet)


urlpatterns = [
    # path("mess/", MessView.as_view())
] + router.urls
