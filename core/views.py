import asyncio
import os
from datetime import datetime, timedelta, timezone

from allauth.account import app_settings as allauth_settings
from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from asgiref.sync import async_to_sync
from dj_rest_auth.registration.views import RegisterView, SocialLoginView
from dj_rest_auth.utils import jwt_encode
from dj_rest_auth.views import PasswordChangeView, PasswordResetView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from jose import JWTError, jwt
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.mixins import ListModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from core.signals import reset_password_signal
from utils.auth.agent_verification import agent_identity_verification
from utils.permissions import IsAgent

from .models import AgentDetails, Profile, User, UserSettings
from .otp import OTPGenerator
from .permissions import IsOwner
from .serializers import *
from .signals import new_user_signal


class GetOTPView(APIView):
    def get(self, request, email):
        user = get_object_or_404(get_user_model(), email=email)
        otp_gen = OTPGenerator(user_id=user.id)

        otp = otp_gen.get_otp()

        return Response({"detail": f"success otp- {otp}"}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    serializer_class = OTPSerializer

    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            get_user_model(), email=serializer.validated_data["email"]
        )
        otp_gen = OTPGenerator(user_id=user.id)

        check = otp_gen.check_otp(serializer.validated_data["otp"])

        if check:
            # Mark user as verified
            user_obj = get_object_or_404(EmailAddress, user=user)

            user_obj.verified = True
            user_obj.save()

            return Response(
                {"detail": "2FA successfully completed"},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response({"detail": "Invalid otp"}, status=status.HTTP_403_FORBIDDEN)


class PasswordResetView(APIView):
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]

            reset_password_signal.send(__class__, email=email)

        return Response(
            {"detail": "otp to reset password has been sent to the provided email"},
            status=status.HTTP_200_OK,
        )


class CustomPasswordResetConfirmView(PasswordChangeView):
    serializer_class = CPasswordChangeSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):

        data = super().get_serializer_context()
        if self.request.method == "POST":

            email = self.request.data["email"]
            user = get_object_or_404(get_user_model(), email=email)
            data["user"] = user
            return data
        return super().get_serializer_context()

    def get_queryset(self):
        return super().get_queryset()


class UserSettingsViewSet(
    ListModelMixin, UpdateModelMixin, GenericViewSet
):  # GenericViewSet
    """
    Users can see and update their settings

    The PATCH endpoint requires that the settings_id is sent as a path parameter


    """

    http_method_names = ["get", "patch"]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSettingsSerializer

    def get_queryset(self):
        return UserSettings.objects.filter(user=self.request.user)


class AgentDetailsView(CreateAPIView):
    """
    Send Agent's Data in for Validation and verification

    Only users that are agent can access this endpoint


    id_type - (Options)

    NIN,
    GOVERNMENT_ID

    """

    permission_classes = [IsAgent]
    serializer_class = AgentDetailsSerializer
    queryset = AgentDetails.objects.none().select_related("user")

    @async_to_sync
    async def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        front_image = serializer.validated_data["id_front"]
        back_image = serializer.validated_data["id_back"]
        selfie_image = serializer.validated_data["photo"]

        agent_verification = await agent_identity_verification(
            front_image, back_image, selfie_image
        )
        if agent_verification:

            # checks if the agent details from identity verification service provider API
            # matches the agent details we've in our DB
            agent_first_name = agent_verification["result"]["firstName"]
            agent_last_name = agent_verification["result"]["lastName"]
            if (
                request.user.first_name.lower() == agent_first_name.lower()
                and request.user.last_name.lower() == agent_last_name.lower()
            ):
                await asyncio.get_event_loop().run_in_executor(None, serializer.save)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED, headers=headers
                )

            return Response(
                data="user details does not match", status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            data="agent verification failed",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def get_serializer_context(self):
        return {"user": self.request.user}


class ProfileViewSet(ModelViewSet):
    http_method_names = ["get", "options", "head", "put"]
    permission_classes = [IsOwner]
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)


class CustomSocialLoginView(SocialLoginView):
    """
    Google Login- Changing the Serializer class to a Custom made one
    """

    serializer_class = CustomSocialLoginSerializer


class CustomRegisterView(RegisterView):
    """
    Register New users
    """

    serializer_class = CustomRegisterSerializer

    # def get_response_data(self, user):

    #     response = super().get_response_data(user)

    #     # Update response to include user's name
    #     user_pk = response["user"]["pk"]
    #     user = get_user_model().objects.get(id=user_pk)
    #     response["user"]["first_name"] = user.first_name
    #     response["user"]["last_name"] = user.last_name
    #     response["user"]["id"] = user.id

    #     return response

    def perform_create(self, serializer):
        user = serializer.save(self.request)

        # Whether to send email after registration
        send_email_check = getattr(settings, "SEND_EMAIL", False)
        new_user_signal.send_robust(__class__, send_email=send_email_check, user=user)

        if (
            allauth_settings.EMAIL_VERIFICATION
            != allauth_settings.EmailVerificationMethod.MANDATORY
        ):
            if getattr(settings, "REST_USE_JWT", False):
                self.access_token, self.refresh_token = jwt_encode(user)
            elif not getattr(settings, "REST_SESSION_LOGIN", False):
                # Session authentication isn't active either, so this has to be
                #  token authentication
                # create_token(self.token_model, user, serializer)
                pass

        return user


# if you want to use Authorization Code Grant, use this
class GoogleLogin(CustomSocialLoginView):
    # Local Development link
    # https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=http://127.0.0.1:8000/accounts/google/login/callback/&prompt=consent&response_type=code&client_id=878674025478-e8s4rf34md8h4n7qobb6mog43nfhfb7r.apps.googleusercontent.com&scope=openid%20email%20profile&access_type=offline

    """
    # Visit this [`link`](https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=https://rentrite.up.railway.app/accounts/google/login/callback/&prompt=consent&response_type=code&client_id=878674025478-e8s4rf34md8h4n7qobb6mog43nfhfb7r.apps.googleusercontent.com&scope=openid%20email%20profile&access_type=offline) for users to see the google account select modal.


    After Users select account for login, they will be redirected to a new url.

    extract the `code` query parameter passed in the redirected url and send to this endpoint to get access and refresh tokens

    Example data:

    {

        code : "4%2F0AWgavdfDkbD_aCXtaruulCuVFpZSEpImEuZouGFZACGO1hxoDwqCV1znzazpn7ev5FmH2w"

    }
    """

    # CALLBACK_URL_YOU_SET_ON_GOOGLE
    default_call_back_url = "http://127.0.0.1:8000/accounts/google/login/callback/"

    adapter_class = GoogleOAuth2Adapter
    callback_url = os.environ.get("CALLBACK_URL", default_call_back_url)

    client_class = OAuth2Client


# I dont think we need this for now


# class SendVerificationTokenView(APIView):
#     """
#     An endpoint that encodes user data and generate JWT token

#     Args:

#         Email

#     Response:

#         HTTP_201_CREATED- if token for user is generated successfully

#     Raise:

#         HTTP_404_NOT_FOUND- if a user with supplied email does not exist
#     """

#     permission_classes = [AllowAny]
#     serializer_class = EmailSerializer

#     def post(self, request):

#         serializer = EmailSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = get_object_or_404(User, email=serializer.validated_data["email"])
#         expiration_time = datetime.now(timezone.utc) + timedelta(seconds=600)
#         encode_user_data = {"user_id": str(user.id), "expire": str(expiration_time)}
#         encoded_jwt = jwt.encode(
#             encode_user_data, settings.SECRET_KEY, algorithm="HS256"
#         )
#         return Response(data=encoded_jwt, status=status.HTTP_201_CREATED)


# class TokenVerificationView(APIView):
#     """
#     An email verification endpoint

#     Args:

#         token

#     Response:

#         HTTP_200_OK- if email verification is successful

#     Raise:

#         HTTP_404_NOT_FOUND- if a user with supplied ID does not exist

#         HTTP_400_BAD_REQUEST- if credential validation is unsuccessful or token has expired
#     """

#     permission_classes = [AllowAny]
#     serializer_class = TokenSerializer

#     def post(self, request):

#         serializer = TokenSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         token = serializer.validated_data["token"]

#         credentials_exception = Response(
#             status=status.HTTP_400_BAD_REQUEST,
#             data="Could not validate credentials",
#         )

#         try:
#             # Decodes token
#             payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
#             user_id: str = payload.get("user_id")
#             expire = payload.get("expire")
#             if user_id is None or expire is None:
#                 raise credentials_exception
#         except JWTError as e:
#             msg = {"error": e, "time": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}

#             return credentials_exception

#         # Check token expiration
#         if str(datetime.now(timezone.utc)) > expire:
#             return Response(
#                 status=status.HTTP_401_UNAUTHORIZED,
#                 data="Token expired or invalid!",
#             )

#         user = get_object_or_404(User, id=user_id)
#         get_allauth = get_object_or_404(EmailAddress, user=user)

#         if get_allauth.verified == True:
#             return Response("email already verified", status=status.HTTP_403_FORBIDDEN)

#         get_allauth.verified = True
#         get_allauth.save()
#         return Response("verification successful", status=status.HTTP_200_OK)
