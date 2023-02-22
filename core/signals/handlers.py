from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.db.models.signals import post_save
from django.dispatch import receiver

from utils.views import mailjet_email_backend

from ..models import Profile, UserSettings
from ..otp import OTPGenerator
from . import new_user_signal, reset_password_signal


@receiver(post_save, sender=get_user_model())
def create_user_profile_and_settings(instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        UserSettings.objects.create(user=instance)


@receiver(new_user_signal)
def send_verification_email(*args, **kwargs):
    if kwargs["send_email"]:
        user = kwargs["user"]
        code = OTPGenerator(user_id=user.id).get_otp()

        # localhost email
        # EmailMessage(
        #     subject="", body="okay", from_email="me@go.com", to=[email]
        # ).send()

        mailjet_email_backend(
            to=user.email,
            subject="Email Verification!",
            text=f"Use this code to verify email address {code} ",
        )


@receiver(reset_password_signal)
def reset_password(**kwargs):
    email = kwargs["email"]

    user = get_user_model().objects.get(email=email)

    code = OTPGenerator(user_id=user.id).get_otp()

    # localhost email
    # EmailMessage(
    #     subject="Password Reset", body=f"Use this code for resetting your password {code}", from_email="me@go.com", to=[email]
    # ).send()

    mailjet_email_backend(
        to=email,
        subject="Password Reset",
        text=f"Use this code for resetting your password {code}",
    )
