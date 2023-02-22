import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'RentRite.settings')

celery = Celery('RentRite')
celery.config_from_object('django.conf:settings', namespace='CELERY')
celery.autodiscover_tasks()