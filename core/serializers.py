from urllib.parse import unquote

from dj_rest_auth.registration.serializers import (
    RegisterSerializer,
    SocialLoginSerializer,
)
from dj_rest_auth.serializers import LoginSerializer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import *


class AgentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDetails

        fields = [
            "nin",
            "id_front",
            "id_back",
            "photo",
            "id_type",
            "phone",
            "certificate",
        ]

    def save(self, **kwargs):

        return super().save(agent=self.context["user"], is_verified=True, **kwargs)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["id", "image", "background_image", "location"]


# For Google Login


class CustomSocialLoginSerializer(SocialLoginSerializer):
    access_token = None
    id_token = None

    def validate(self, attrs):
        # update the received code to a proper format. so it doesn't throw error.

        attrs["code"] = unquote(attrs.get("code"))

        return super().validate(attrs)


class CustomLoginSerializer(LoginSerializer):
    username = None  # Remove username from the login


class CustomRegisterSerializer(RegisterSerializer):
    username = None
    first_name = serializers.CharField(max_length=250)
    last_name = serializers.CharField(max_length=250)
    is_agent = serializers.BooleanField(required=False)

    def custom_signup(self, request, user):
        user_obj = get_user_model().objects.get(email=user)

        user_obj.first_name = request.data.get("first_name", "")
        user_obj.last_name = request.data.get("last_name", "")
        user_obj.is_agent = bool(request.data.get("is_agent", False))
        user_obj.save()

        pass


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["id", "name", "email", "is_agent", "date_joined", "status", "phone"]

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, obj):
        return obj.get_full_name()

    @extend_schema_field(OpenApiTypes.STR)
    def get_status(self, obj):
        try:
            if obj.is_agent:
                status = obj.agent_details.is_verified
                return "Verified" if status else "Unverified"
        except:
            return None

    @extend_schema_field(OpenApiTypes.STR)
    def get_phone(self, obj):
        try:
            if obj.is_agent:
                return str(obj.agent_details.phone)
        except:
            return None


class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ["id", "language", "theme", "notification"]


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        if get_user_model().objects.filter(email=email):
            return email
        raise serializers.ValidationError()


class CPasswordChangeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    old_password = serializers.CharField(max_length=128)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    set_password_form_class = SetPasswordForm

    set_password_form = None

    def __init__(self, *args, **kwargs):
        self.old_password_field_enabled = getattr(
            settings,
            "OLD_PASSWORD_FIELD_ENABLED",
            False,
        )
        self.logout_on_password_change = getattr(
            settings,
            "LOGOUT_ON_PASSWORD_CHANGE",
            False,
        )
        super().__init__(*args, **kwargs)

        if not self.old_password_field_enabled:
            self.fields.pop("old_password")

        self.request = self.context.get("request")
        self.user = self.context.get("user")

    def validate_old_password(self, value):
        invalid_password_conditions = (
            self.old_password_field_enabled,
            self.user,
            not self.user.check_password(value),
        )

        if all(invalid_password_conditions):
            err_msg = _(
                "Your old password was entered incorrectly. Please enter it again."
            )
            raise serializers.ValidationError(err_msg)
        return value

    def custom_validation(self, attrs):
        pass

    def validate(self, attrs):
        self.set_password_form = self.set_password_form_class(
            user=self.user,
            data=attrs,
        )

        self.custom_validation(attrs)
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        self.set_password_form.save()
        if not self.logout_on_password_change:
            from django.contrib.auth import update_session_auth_hash

            update_session_auth_hash(self.request, self.user)
