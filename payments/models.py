from django.db import models
from django.contrib.auth import get_user_model
import secrets
from payments.paystack import Paystack

PAYMENT_OPTION_CHOICES = (
	('paystack', 'paystack'),
	('flutterwave', 'flutterwave'),
)
PAYMENT_PLANS_CHOICES = (
	('Standard 1', 'Standard 1'),
	('Standard 2', 'Standard 2'),
	('Standard 3', 'Standard 3'),
	('Gold 1', 'Gold 1'),
	('Gold 2', 'Gold 2')
)
class Payment(models.Model):
	user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, blank=True, null=True)
	email = models.EmailField()
	amount = models.FloatField()
	txn_ref = models.CharField(max_length=200, unique=True)
	verified = models.BooleanField(default=False)
	payment_options = models.CharField(max_length=255, choices=PAYMENT_OPTION_CHOICES)
	payment_plan = models.CharField(max_length=255, choices=PAYMENT_PLANS_CHOICES)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	metadata = models.JSONField()

	class Meta:
		ordering = ('-created_at',)
		verbose_name_plural = 'Payments'

	def __str__(self):
		return f"Payment of {self.amount} by {self.user} on {self.created_at}"

	def save(self, *args, **kwargs):
		if not self.txn_ref:
			self.txn_ref = secrets.token_urlsafe(50)
		super().save(*args, **kwargs)

	def verify_paystack_payment(self):
		paystack = Paystack()
		status, result = paystack.verify_payment(self.txn_ref, self.amount)
		if not status:
			return False
		if result['amount'] / 100 != self.amount:
			print(result['amount'], self.amount)
			return False
		self.verified = True
		self.save()
		return True

class Wallet(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(default=0)
    currency = models.CharField(default="NGN", max_length=100)

    def __str__(self):
        return f'{self.user}: {self.balance} {self.currency}'