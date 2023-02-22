from rest_framework import serializers
from .models import Payment
# from django.contrib.auth.models import User
from core.models import User
from django.conf import settings
import requests

class PaystackPaymentSerializer(serializers.ModelSerializer):
	amount = serializers.IntegerField()
	email = serializers.EmailField()

	class Meta:
		model = Payment
		fields = ['amount', 'email', 'metadata']

	def validate_email(self, value):
		if User.objects.filter(email=value).exists():
			return value
		raise serializers.ValidationError({"detail": "Email not found"})

class CreateCardDepositFlutterwaveSerializer(serializers.Serializer):
	amount = serializers.IntegerField()
	email = serializers.EmailField()
	metadata = serializers.JSONField()
	payment_plan = serializers.CharField()
	
	def validate(self, data):
		amount = data.get("amount")
		email = data.get("email")
		metadata = data.get("metadata")
		payment_plan = data.get("payment_plan")

		if amount is None:
			raise serializers.ValidationError("amount is required")
		
		if email is None:
			raise serializers.ValidationError("email is required")
		
		if payment_plan is None:
			raise serializers.ValidationError("payment plan is required")

		if metadata is None:
			raise serializers.ValidationError("metadata is required")
		
		return data