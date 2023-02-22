from celery import shared_task
import requests


@shared_task
def perform_click(scheme, domain, id):
    requests.get(f"{scheme}://{domain}/clicks/count/{id}/")
    print(f'Apartment {id} have just been viewed')
