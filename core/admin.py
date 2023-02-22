from django.contrib import admin
from .models import User, AgentDetails
# Register your models here.

admin.site.register([User, AgentDetails]) 