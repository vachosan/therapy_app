from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import TherapistProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = UserAdmin.list_filter + ("role",)


@admin.register(TherapistProfile)
class TherapistProfileAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "slug",
        "user",
        "specialization",
        "accepts_new_clients",
        "is_verified",
        "updated_at",
    )
    list_filter = ("accepts_new_clients", "is_verified", "specialization")
    search_fields = ("display_name", "slug", "user__username", "user__email", "specialization")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("display_name",)}
    fieldsets = (
        ("Uživatel", {"fields": ("user",)}),
        ("Profil", {"fields": ("display_name", "slug", "bio", "specialization")}),
        ("Stav", {"fields": ("accepts_new_clients", "is_verified")}),
        ("Časové údaje", {"fields": ("created_at", "updated_at")}),
    )
