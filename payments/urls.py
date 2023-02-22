from django.urls import path
from . import views

urlpatterns = [
	path('pay/card-deposit-flutterwave/', views.flutterwave_card_deposit),
    path('flw-deposit/verify/', views.flutterwave_confirm_card_deposit),
	
	path('pay/card-deposit-paystack/', views.paystack_card_deposit),
    path('paystack-deposit/verify/', views.verify_paystack_payment),
]
