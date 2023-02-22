import requests
from django.http.request import HttpRequest
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from core.permissions import IsFileOwner, IsOwner
from utils.permissions import IsAgent

from .filters import ApartmentFilter
from .models import Apartment, Bookmark, Media, Picture, Review
from .serializers import *
from .tasks import perform_click


class ApartmentViewSet(ModelViewSet):
    """
    Agent can create apartment and also make edits to previously uploaded apartments

    Apartments can be searched by its location, price, category and title.


    It can also be filtered based on any these attributes.

    Args:
        ModelViewSet (_type_): _description_

    Returns:
        _type_: _description_
    """

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ApartmentFilter
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsOwner, IsAgent]
    search_fields = ["location", "price", "category", "title"]
    ordering_fields = ["category"]

    @action(methods=["GET"], permission_classes=[IsAuthenticated], detail=False)
    def mine(self, request):
        """
        Returns all the apartments owned by the currently logged in agent

        """
        my_apartments = Apartment.objects.filter(
            agent=self.request.user
        ).prefetch_related("reviews", "pictures", "videos")

        serializer = ApartmentSerializer(my_apartments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ApartmentSerializer
        return CreateApartmentSerializer

    def get_serializer_context(self):
        return {"user": self.request.user, "request": self.request}

    def get_queryset(self):
        return (
            Apartment.objects.all()
            .prefetch_related("reviews", "pictures", "videos")
            .select_related("agent")
        )

    def retrieve(self, request: HttpRequest, *args, **kwargs):

        # simulate getting this endpoint so that it can trigger the views count.
        domain = request.get_host()
        id = kwargs["pk"]
        scheme = request.scheme

        requests.get(f"{scheme}://{domain}/clicks/count/{id}/")

        # to make it a background task
        # perform_click.delay(scheme, domain, id)

        return super().retrieve(request, *args, **kwargs)


class PicturesViewSet(ModelViewSet):
    """
    Pictures of the apartment can be uploaded

    Args:
        The apartment_id

    To post pictures, gather the images files in a form data Array

    """

    http_method_names = ["get", "post", "delete"]
    queryset = Picture.objects.none()
    permission_classes = [IsFileOwner, IsAgent]
    serializer_class = PictureSerializer

    def get_queryset(self):
        if pk := self.kwargs.get("apartment_pk", ""):
            return Picture.objects.filter(apartment_id=pk).select_related("apartment")
        return super().get_queryset()

    def get_serializer_context(self):
        if pk := self.kwargs.get("apartment_pk", ""):
            return {"apartment_pk": pk, "request": self.request}
        return super().get_serializer_context()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreatePictureSerializer
        return PictureSerializer

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        # Since the images are returning null values in Response due to bulk_create,
        # a nice success message should suffice instead of instances of the newly uploaded images
        return Response(
            {"detail": "Images uploaded successfully"}, status=status.HTTP_201_CREATED
        )


class MediaViewSet(ModelViewSet):

    """
    Short video clips of the apartment can be uploaded

    Replaced and removed

    Args:
        The apartment_id


    """

    http_method_names = ["get", "post", "delete"]
    queryset = Media.objects.none()
    permission_classes = [IsFileOwner, IsAgent]
    serializer_class = MediaSerializer

    def get_queryset(self):
        if pk := self.kwargs.get("apartment_pk", ""):
            return Media.objects.filter(apartment_id=pk)
        return super().get_queryset()

    def get_serializer_context(self):
        if pk := self.kwargs.get("apartment_pk", ""):
            return {"apartment_pk": pk, "request": self.request}
        return super().get_serializer_context()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateMediaSerializer
        return MediaSerializer

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        # Since the videos are returning null values in Response due to bulk_create,
        # a nice success message should suffice instead of instances of the newly uploaded images
        return Response(
            {"detail": "Videos uploaded successfully"}, status=status.HTTP_201_CREATED
        )


class ReviewViewSet(ModelViewSet):
    """
    Agents and other users can leave reviews on apartments

    They can update and delete their reviews


    """

    http_method_names = ["get", "post", "put", "delete"]
    queryset = Review.objects.none()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        if pk := self.kwargs.get("apartment_pk", ""):
            return Review.objects.filter(apartment_id=pk)
        return super().get_queryset()

    def get_serializer_context(self):
        if pk := self.kwargs.get("apartment_pk", ""):
            return {"apartment_pk": pk, "user": self.request.user}
        return super().get_serializer_context()


class BookmarkView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateBookmarkSerializer

    def get(self, request):

        """
        Provides all the apartments that have been saved by the currently logged in user
        """

        my_bookmark = Bookmark.objects.filter(user=request.user).values("apartment_id")

        _ids = [item["apartment_id"] for item in my_bookmark]

        apartments = Apartment.objects.filter(id__in=_ids)

        serializer = ApartmentSerializer(apartments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Add an apartment to bookmark or saved apartment

        Args:

            request: Should contain the Bearer(JWT Token) in the Authorization Header

            apartment_id: The id of the apartment to be saved

        Returns:

            instance: new Bookmark

            status_code: 201
        """

        instance = Bookmark.objects.create(
            user=request.user, apartment_id=request.data["apartment_id"]
        )
        serializer = CreateBookmarkSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """
        Delete selected bookmarks

        Args:

            request: Should contain the Bearer(JWT Token) in the Authorization Header

            apartment_id: An array of the ids' of the apartment to be deleted

        Example request body:

            {
                "items" : [

                    "c0330839-f30c-4667-951c-2811e5e09bdf",

                    "d59a5194-2cab-4e1c-8642-d549f5c65b86"
                ]
            }

        """

        aparment_id_list = request.data["items"]

        Bookmark.objects.filter(apartment_id__in=aparment_id_list).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
