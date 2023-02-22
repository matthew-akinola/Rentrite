from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from payments.models import Wallet
from .models import Profile
from mailjet_rest import Client
from django.conf import settings


@receiver(post_save, sender = get_user_model())
def create_user_profile(instance, created, **kwargs):
    if created:
        Profile.objects.create(user = instance)
@receiver(post_save, sender = get_user_model())
def create_user_wallet(instance, created, **kwargs):
    if created:
        Wallet.objects.create(user = instance)

@receiver(post_save, sender = get_user_model())
def send_confirmation_email(instance, created, **kwargs):
    pass
    #Not for Now 
    # if created:

        
    #     api_key = settings.MJ_APIKEY_PUBLIC
    #     api_secret = settings.MJ_APIKEY_PRIVATE
    #     mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    #     data = {
    #     'Messages': [
    #         {
    #         "From": {
    #             "Email": "$SENDER_EMAIL",
    #             "Name": "Me"
    #         },
    #         "To": [
    #             {
    #             "Email": instance.email,
    #             "Name": instance.get_full_name()
    #             }
    #         ],
    #         "Subject": "Email Confirmation",
    #         "TextPart": "",
    #         "HTMLPart": "<h3>Dear passenger 1, welcome to <a href=\"https://www.mailjet.com/\">Mailjet</a>!</h3><br />May the delivery force be with you!"
    #         }
    #     ]
    #     }
    #     mailjet.send.create(data=data)
