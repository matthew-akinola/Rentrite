import json
from django.conf import settings
import requests

class Paystack:
    PAYSTACK_SK = settings.PAYSTACK_SECRET_KEY
    base_url = "https://api.paystack.co/"

    def verify_payment(self, ref, *args, **kwargs):
        path = f'transaction/verify/{ref}'
        headers = {
            "Authorization": f"Bearer {self.PAYSTACK_SK}",
            "Content-Type": "application/json",
        }
        url = self.base_url + path
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print(f"Http Error: {errh}")
            return False, f"Http Error: {errh}"
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
            return False, f"Error Connecting: {errc}"
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}")
            return False, f"Timeout Error: {errt}"
        except requests.exceptions.RequestException as err:
            print(f"Something went wrong: {err}")
            return False, f"Something went wrong: {err}"
        else:
            response_data = response.json()
            if response.status_code == 200:
                return response_data['status'], response_data['data']
            else:
                print(response_data)
                return response_data['status'], response_data['message']
