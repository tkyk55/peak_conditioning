from django.contrib import admin
from .models import Booking, ExBooking
from .models import Master, EmailTemplate

#admin.site.register(Staff)
admin.site.register(Booking)
admin.site.register(ExBooking)
admin.site.register(Master)
#admin.site.register(Notification)

admin.site.register(EmailTemplate)