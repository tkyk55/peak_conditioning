from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser
from .models import Training

class CustomUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Peak_condition dates', {'fields': ('first_name', 'last_name', 'sex', 'birthday', 'tel_number', 'num_contracts', 'num_times', 'stat_date', 'end_date', 'is_shoes_custody', 'amount_money', 'memo', 'created')}),
        ('Personal info', {'fields': ('member_no', 'email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),

    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'email_verified', 'is_staff')
    search_fields = ('email',)
    ordering = ('email',)

    def email_verified(self, obj):
        email_address = obj.emailaddress_set.filter(email=obj.email).first()
        return email_address.verified if email_address else False
    email_verified.boolean = True
    email_verified.short_description = 'Email verified'

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Training)