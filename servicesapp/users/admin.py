from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    # -------------------------
    # List display (table view)
    # -------------------------
    list_display = (
        "email",
        "full_name",
        "role",
        "phone_number",
        "is_staff",
        "is_active",
        "is_verified",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
        "is_verified",
    )

    search_fields = (
        "email",
        "full_name",
        "phone_number",
    )

    ordering = ("email",)

    # -------------------------
    # Field layout (edit page)
    # -------------------------
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "phone_number", "role", "profile_picture", "address","skill")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Location Info", {"fields": ("latitude", "longitude")}),
        ("Extra Info", {"fields": ("is_verified", "agree_to_terms", "terms_accepted_at", "date_joined")}),
        
    )

    # -------------------------
    # Create user form layout
    # -------------------------
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "full_name",
                "phone_number",
                "role",
                "password1",
                
                "is_staff",
                "is_active",
            ),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")
