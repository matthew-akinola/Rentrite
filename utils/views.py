from decouple import config
from django.conf import settings
from hitcount.views import HitCountDetailView
from mailjet_rest import Client

from apartments.models import Apartment


# To make the hitcount work.
class ApartmentClicks(HitCountDetailView):
    model = Apartment
    count_hit = True
    template_name = "apartment_detail.html"


def mailjet_email_backend(
    to: str,
    subject: str,
    text: str,
    name: str = None,
    html_part: str = None,
    template_id: int = None,
    **kwargs
):
    try:
        api_key = settings.MJ_API_KEY
        api_secret = settings.MJ_API_SECRET
        mailjet = Client(auth=(api_key, api_secret), version="v3.1")

        data = {
            "Messages": [
                {
                    "From": {
                        "Email": config("OFFICIAL_EMAIL", "blazingkrane@gmail.com"),
                        "Name": "RentRite",
                    },
                    "To": [
                        {
                            "Email": to,
                            "Name": name,
                        }
                    ],
                    "Subject": subject,
                    "TextPart": text,
                    "HTMLPart": html_part,
                    "CustomCampaign": "SendAPI_campaign",
                    # "DeduplicateCampaign": True
                }
            ]
        }

        result = mailjet.send.create(data=data)
        print({"status": result.status_code})
        print(result.json())
    except:

        print("Something went wrong with email messaging")
