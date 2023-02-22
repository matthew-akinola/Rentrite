import json
from uuid import UUID

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.contrib.auth import get_user_model

from core.serializers import UserSerializer

from .models import Conversation, Message
from .serializers import MessageSerializer


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


class ChatConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.user = None
        self.conversation_name = None
        self.conversation = None
        self.message = None

    @classmethod
    def encode_json(cls, content):
        return json.dumps(content, cls=UUIDEncoder)

    def connect(self):
        self.user = self.scope["user"]

        if not self.user:
            self.close()

        self.accept()

        # Retrieve the conversation name from the url format( firstname_lastname__firstname_lastname )
        self.conversation_name = (
            f"{self.scope['url_route']['kwargs']['conversation_name']}"
        )

        self.conversation, created = Conversation.objects.get_or_create(
            name=self.conversation_name
        )

        async_to_sync(self.channel_layer.group_add)(
            self.conversation_name, self.channel_name
        )

        # When a user comes online
        async_to_sync(self.channel_layer.group_send)(
            self.conversation_name,
            {"type": "user.join", "user": UserSerializer(self.user).data},
        )

        self.conversation.join(self.user)

        # Get users that are online
        self.send_json(
            {
                "type": "online_user_list",
                "users": [
                    UserSerializer(user).data for user in self.conversation.online.all()
                ],
                "current_user": UserSerializer(self.user).data,
            }
        )

        messages = self.conversation.messages.all().order_by("-timestamp")[0:50]
        message_count = self.conversation.messages.all().count()

        self.send_json(
            {
                "type": "last_50_messages",
                "messages": MessageSerializer(messages, many=True).data,
                "has_more": message_count > 50,
            }
        )

    def disconnect(self, code):
        if self.user:
            self.conversation.leave(self.user)

            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "user.leave",
                    "user": UserSerializer(self.user).data,
                },
            )
        # May be removed since it might prevent a user from getting any messages or notifications when disconnected
        async_to_sync(self.channel_layer.group_discard)(
            self.conversation_name, self.channel_name
        )

        return super().disconnect(code)

    def receive_json(self, content, **kwargs):
        message_type = content.get("type", "")
        attachment = content.get("attachment", False)

        if message_type == "chat_message":

            message = Message.objects.create(
                from_user=self.user,
                to_user=self.get_receiver(),
                text=content["message"],
                conversation=self.conversation,
            )

            #instantiate the init value so it can be accessed
            self.message = message

            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": (
                        "echo.message.attachment" if attachment else "echo.message"
                    ),
                    "message": MessageSerializer(message).data,
                },
            )

        if message_type == "typing":
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "user.typing",
                    "user": UserSerializer(self.user).data,
                    "action": self.user.get_full_name() + " is typing",
                },
            )

        if message_type == "recording":
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "user.recording",
                    "user": UserSerializer(self.user).data,
                    "action": self.user.get_full_name() + " is recording",
                },
            )

        if message_type == "read_messages":
            messages_to_me = self.conversation.messages.filter(to_user=self.user)
            messages_to_me.update(read=True)

            # Update the unread message count
            unread_count = Message.objects.filter(to_user=self.user, read=False).count()
            async_to_sync(self.channel_layer.group_send)(
                # self.user.get_full_name() + "__notifications",
                self.conversation_name,
                {
                    "type": "unread.count",
                    "unread_count": unread_count,
                },
            )

    # ______________________________________________________________________________________#
    # __________________________________HANDLERS___________________________________________
    # _______________________________________________________________________________________#

    def echo_message(self, event):
        # The group_send will call this function and rebroadcast the message to the group

        self.send_json(event)

    def echo_message_attachment(self, event):
        # The group_send will call this function and rebroadcast the message to the group
        # Trying to hold the connection till an attachment is added with normal http request...Not workig for now since it will block other usrs from conecting
        # ________Possible solutions
        # (1) Use celery to run it as a background task
        # (2) Attempt to use AsyncWebsocket to avoid blocking
        # (3) Try sending attachments over the websocket connection [(issue--It is not proper to send large binary data over a websocket connection)]

        import time

        while bool(self.message.attachment.first()) == False:
            time.sleep(1)

        event["message"] = MessageSerializer(self.message).data
        self.send_json(event)

    def user_join(self, event):
        # This handler is called when a user comes online
        self.send_json(event)

    def user_leave(self, event):
        # This handler is called when a user goes offline
        self.send_json(event)

    def user_typing(self, event):
        self.send_json(event)

    def user_recording(self, event):
        self.send_json(event)

    def unread_count(self, event):
        # Number of unread messages
        self.send_json(event)

    def get_receiver(self):
        User = get_user_model()

        names = self.conversation_name.split("__")

        names = [name.replace("_", " ").lower() for name in names]

        for name in names:

            if name != self.user.get_full_name().lower():

                first_name, last_name = name.split()

                user = User.objects.filter(
                    first_name__iexact=first_name, last_name__iexact=last_name
                ).first()

                return user
