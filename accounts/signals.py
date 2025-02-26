from allauth.account.signals import email_confirmed
from django.dispatch import receiver
from .models import CustomUser

@receiver(email_confirmed)
def email_confirmed_(request, email_address, **kwargs):
    user = email_address.user
    user.email_verified = True
    user.save()
