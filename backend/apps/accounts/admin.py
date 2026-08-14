from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Organization, User


class UserAdmin(DjangoUserAdmin):
    # Adds organization to the existing fieldsets rather than replacing them, so the
    # stock auth fields (permissions, password change, …) stay intact.
    fieldsets = DjangoUserAdmin.fieldsets + (("Organization", {"fields": ("organization",)}),)
    list_display = DjangoUserAdmin.list_display + ("organization",)


admin.site.register(User, UserAdmin)
admin.site.register(Organization)
