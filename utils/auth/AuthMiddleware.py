import time

import jwt
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser


def is_token_expired(decoded_token):

    if "exp" in decoded_token:
        exp = decoded_token["exp"]
        if isinstance(exp, int):
            return exp >= time.time()


async def get_user(user_id):
    try:
        user = await get_user_model().objects.aget(id=user_id)
        return user
    except get_user_model().DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleWareStack(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        if b"authorization" in headers:
            prefix, token = headers[b"authorization"].decode().split()
            if prefix == settings.SIMPLE_JWT["AUTH_HEADER_TYPES"][0]:
                try:
                    decoded_data = jwt.decode(
                        token, settings.SECRET_KEY, algorithms=["HS256"]
                    )
                except (jwt.DecodeError, jwt.ExpiredSignatureError):
                    decoded_data = dict()

                if is_token_expired(decoded_data):
                    scope["user"] = await get_user(decoded_data["user_id"])

        return await super().__call__(scope, receive, send)
