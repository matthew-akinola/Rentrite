# (Arrange, Act, Assert) - AAA

import random

import pytest
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient
# from rest_framework.test import 

from apartments.models import Apartment
from core.models import User


@pytest.mark.django_db
class TestApartmentCreation:
    def test_if_user_is_not_agent_returns_401(self, api_client: APIClient):

        api_client.force_authenticate(user=User(is_agent=True))
        resp = api_client.post(
            "/apartment/",
            {
                "title": "string",
                "category": "Bungalow",
                "price": random.randint(250, 400),
                "locality": "string",
                "state": "string",
                "area": "string",
                "street": "string",
                "specifications": {
                    "additionalProp1": "string",
                    "additionalProp2": "string",
                    "additionalProp3": "string",
                },
                "descriptions": "string",
                "is_available": True,
            },
            format="json",
        )

        assert resp.status_code == 201 # status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestApartmentSearch:
    def test_if_users_are_authenticated_returns_401(self, api_client: APIClient):

        response = api_client.get("/apartment/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_authenticated_users_can_view_apartments_returns_200(
        self, api_client: APIClient
    ):

        api_client.force_authenticate(user=User())

        response = api_client.get("/apartment/")

        assert response.status_code == status.HTTP_200_OK

    def test_viewing_an_apartment_detail_returns_200(self, api_client: APIClient):

        apartment = baker.make(Apartment)

        api_client.force_authenticate(user=User())
        response = api_client.get(f"/apartment/{apartment.id}/")

        assert response.status_code == status.HTTP_200_OK
