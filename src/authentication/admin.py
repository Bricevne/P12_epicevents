from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from authentication.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Class managing custom users in admin panel."""

    list_display = ['id', 'first_name', 'last_name', "role"]
    list_filter = ["role"]

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'role', 'password1', 'password2')}
        ),
    )

    search_fields = ['first_name']
    ordering = ['first_name']
