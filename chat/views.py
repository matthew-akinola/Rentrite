from django.db.models import Q
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .models import Attachment, Conversation, Message
from .paginators import MessagePagination
from .serializers import AttachmentSerializer, ConversationSerializer, MessageSerializer, CreateAttachmentSerializer


class MessageViewSet(ListModelMixin, DestroyModelMixin, GenericViewSet):  #
    """
    To get message between two users, send the conversation_name as a query parameter

    Example:
        http://domain/chat/messages?conversation=Hussein_Ibrahim__Admin_Man

    Args:
        conversation: str


    """

    serializer_class = MessageSerializer
    queryset = Message.objects.none()
    pagination_class = MessagePagination

    def get_queryset(self):
        conversation_name = self.request.GET.get("conversation", "")

        queryset = (
            Message.objects.filter(
                Q(conversation__name__icontains=self.request.user.first_name)
                & Q(conversation__name__icontains=self.request.user.last_name)
            )
            .filter(conversation__name=conversation_name)
            .order_by("-timestamp")
        )
        return queryset


class ConversationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = ConversationSerializer
    queryset = Conversation.objects.none()
    lookup_field = "name"

    def get_queryset(self):
        queryset = Conversation.objects.filter(
            name__contains=self.request.user.first_name
        )
        return queryset

    def get_serializer_context(self):
        return {"request": self.request, "user": self.request.user}


class AttachmentViewSet(CreateModelMixin, GenericViewSet):
    queryset = Attachment.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateAttachmentSerializer
        return AttachmentSerializer