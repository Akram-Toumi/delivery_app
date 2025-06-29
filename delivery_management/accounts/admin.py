# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Show these fields in the user list in admin
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'is_active_driver')
    
    # Add 'role', 'phone', 'avatar', 'is_active_driver' to the edit form
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone', 'avatar', 'is_active_driver'),
        }),
    )
    
    # Add custom fields to the "Add user" form as well
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone', 'avatar', 'is_active_driver'),
        }),
    )

admin.site.register(User, CustomUserAdmin)
