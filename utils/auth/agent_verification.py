import os

import httpx
from decouple import config

FACEKI_ID = os.environ.get("FACEKI_ID", config("FACEKI_ID", ""))
FACEKI_EMAIL = os.environ.get("FACEKI_EMAIL", config("FACEKI_EMAIL", ""))


async def agent_identity_verification(front_image, back_image, selfie_image):

    body = {"client_id": FACEKI_ID, "email": FACEKI_EMAIL}
    async with httpx.AsyncClient() as client:

        get_token = await client.post(
            url="https://app.faceki.com/getToken", json=body, timeout=None
        )
        body = {
            "doc_front_image": front_image,
            "doc_back_image": back_image,
            "selfie_image": selfie_image,
        }

        if get_token.json():
            token = get_token.json()["token"]

            verify_agent_details = await client.post(
                url="https://app.faceki.com/kyc-verification",
                headers={"Authorization": f"Bearer {token}"},
                files=body,
                timeout=None,
            )

            verify_agent_details = verify_agent_details.json()
            status = verify_agent_details.get("status", "")
            if status:
                return None

            return verify_agent_details

        return None
