from rest_framework import serializers

from .models import Message, Conversation, Attachment
from core.serializers import UserSerializer
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

User = get_user_model()
class CreateAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attachment
        fields = ['id', '_file', 'message']

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', '_file']

class MessageSerializer(serializers.ModelSerializer):
    from_user = UserSerializer()
    to_user = UserSerializer()
    conversation = serializers.SerializerMethodField()
    attachment = AttachmentSerializer(many = True)

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "from_user",
            "to_user",
            "text",
            "attachment",
            "timestamp",
            "read",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_conversation(self, obj: Message):
        return str(obj.conversation.id)

    
    




class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "name", "other_user", "last_message")

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_last_message(self, obj):
        messages = obj.messages.all().order_by("-timestamp")
        if not messages.exists():
            return None
        message = messages[0]
        return MessageSerializer(message).data
        
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_other_user(self, obj):
        User = get_user_model()

        names = obj.name.split("__")

        names = [name.replace("_", " ").lower() for name in names]

        for name in names:

            if name != self.context['user'].get_full_name().lower():

                first_name, last_name = name.split()

                user = User.objects.filter(
                    first_name__iexact=first_name, last_name__iexact=last_name
                ).first()

                return UserSerializer(user).data