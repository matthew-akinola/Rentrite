from django.contrib import admin
from .models import Bookmark, Apartment, Picture, Media


admin.site.register([Bookmark, Apartment, Picture, Media])
