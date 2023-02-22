import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from utils.paths.path_helpers import get_passport_path
from utils.validators.models import validate_NIN_digits, validate_file_size

from .managers import CustomUserManager

# Create your models here.
from channels.db import database_sync_to_async

GENDER_CHOICES = [
    ("M", "Male"),
    ("F", "Female"),
]
ID_TYPE_CHOICES = [("NIN", "NIN"), ("GOVERNMENT_ID", "GOVERNMENT_ID")]

class User(AbstractUser):
    username = None
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    email = models.EmailField(unique=True)
    is_agent = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


class Profile(models.Model):

    image = models.ImageField(default="default.jpg", upload_to="profile_pictures")
    background_image = models.ImageField(
        default="default_id.png", upload_to="background_images"
    )
    phone = PhoneNumberField(blank=True, null=True)
    location = models.CharField(max_length=550, blank=True, null=True)
    country = models.CharField(max_length=250, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now_add=True)


class AgentDetails(models.Model):

    nin = models.CharField(
        max_length=11,
        validators=[MinLengthValidator(11), validate_NIN_digits],
        null=True,
        blank=True,
    )
    id_front = models.ImageField(
        upload_to=get_passport_path,
        null=True,
        blank=True,
        verbose_name="Goverment ID Front",
        validators=[validate_file_size]
    )
    id_back = models.ImageField(
        upload_to=get_passport_path,
        null=True,
        blank=True,
        verbose_name="Goverment ID Back",
        validators=[validate_file_size]

    )
    photo = models.ImageField(upload_to=get_passport_path)
    id_type = models.CharField(choices=ID_TYPE_CHOICES, max_length=50)
    phone = PhoneNumberField()
    is_verified = models.BooleanField(default=False)
    certificate = models.ImageField(upload_to='certificates/', null=True, blank=True)

    agent = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="agent_details"
    )

    class Meta:
        verbose_name = "Agent Detail" # verbose_name_plural meta option will just add an 's' to this 


class UserSettings(models.Model):
    THEME = [
        ('light', 'light'),
        ('dark', 'dark')
    ]

    language = models.CharField(default="English", max_length=200)
    theme = models.CharField(max_length=200, default='light', choices=THEME)
    notification = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class OTP(models.Model):
    counter = models.IntegerField(default=1)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    