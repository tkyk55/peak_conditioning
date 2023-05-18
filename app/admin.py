from django.contrib import admin
from .models import Staff, Booking, ExBooking, Master ,Notification

admin.site.register(Staff)
admin.site.register(Booking)
admin.site.register(ExBooking)
admin.site.register(Master)
admin.site.register(Notification)
