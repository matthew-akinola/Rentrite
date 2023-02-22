from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.serializers import UserSerializer

from .models import Apartment, Bookmark, Media, Picture, Review


class CreateBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ["id", "apartment_id"]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "text", "date_created"]

    def save(self, **kwargs):
        user = self.context["user"]
        return super().save(user=user, **self.validated_data)


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ["id", "video"]

    def save(self, **kwargs):
        _id = self.context["apartment_pk"]
        return super().save(apartment_id=_id, **self.validated_data)

    def get_video(self, obj: Media):
        return self.context["request"].build_absolute_uri(obj.video.url)


class CreateMediaSerializer(serializers.Serializer):
    video = serializers.ListField(child=serializers.FileField(), allow_empty = False)


    def create(self, validated_data):

        videos = validated_data.pop("video")

        vids = [
            Media(video=vid, apartment_id=self.context["apartment_pk"])
            for vid in videos
        ]

        instance = Media.objects.bulk_create(vids)

        # Since the `instance` is a list, a key has to be assigned to the instance so it can be accessed in the View Response

        return {"video": instance}


class PictureSerializer(serializers.ModelSerializer):
    # image = serializers.SerializerMethodField()

    class Meta:
        model = Picture
        fields = ["id", "image"]  # "cover_pic"

    def get_image(self, obj: Picture):
        # obj.apartment.
        return self.context["request"].build_absolute_uri(obj.image.url)


class CreatePictureSerializer(serializers.Serializer):
    """
    ListField -- A field class that validates a list of objects.

    Signature: ListField(child=<A_FIELD_INSTANCE>, allow_empty=True, min_length=None, max_length=None)

        child - A field instance that should be used for validating the objects in the list. If this argument is not provided then objects in the list will not be validated.
        allow_empty - Designates if empty lists are allowed.
        min_length - Validates that the list contains no fewer than this number of elements.
        max_length - Validates that the list contains no more than this number of elements.
    
    """

    image = serializers.ListField(child=serializers.ImageField(), allow_empty = False)

    def create(self, validated_data):

        images = validated_data.pop("image")

        pics = [
            Picture(image=img, apartment_id=self.context["apartment_pk"])
            for img in images
        ]

        instance = Picture.objects.bulk_create(pics)

        # Since the `instance` is a list, a key has to be assigned to the instance so it can be accessed in the View Response

        return {"image": instance}


class CreateApartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartment
        fields = [
            "id",
            "title",
            "category",
            "_type",
            "price",
            "address",
            "state",
            "map_link",
            "specifications",
            "descriptions",
            "is_available",
        ]

    def save(self, **kwargs):
        user = self.context["user"]
        return super().save(agent=user, **self.validated_data)


class ApartmentSerializer(serializers.ModelSerializer):
    # apartment_type = serializers.CharField(source = '_type')
    agent = UserSerializer(read_only=True)
    pictures = PictureSerializer(many=True)
    videos = MediaSerializer(many=True)
    clicks = serializers.SerializerMethodField()
    verified = serializers.BooleanField(read_only=True)
    # cover_pic = serializers.SerializerMethodField()

    class Meta:
        model = Apartment
        fields = [
            "id",
            "property_ref",
            "title",
            "category",
            "_type",
            "price",
            "state",
            "address",
            "map_link",
            "specifications",
            "descriptions",
            "is_available",
            "verified",
            "clicks",
            "agent",
            "pictures",
            # "cover_pic",
            "videos",
        ]

    # def get_cover_pic(self, apartment:Apartment):

    #     obj = apartment.cover_pic()

    #     try:
    #         return  obj.id # self.context['request'].build_absolute_uri(obj.image.url)
    #     except:
    #         return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_clicks(self, apartment):
        return apartment.hit_count.hits
