from django.contrib import admin
from .models import CustomUser
from .models import Training

admin.site.register(CustomUser)
admin.site.register(Training)

