from django.contrib import admin
from .models import ArtisanApplication, ArtisanDocument


class ArtisanDocumentInline(admin.TabularInline):
    model = ArtisanDocument
    extra = 0
    readonly_fields = ("uploaded_at",)


@admin.register(ArtisanApplication)
class ArtisanApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone_number",
        "skill_category",
        "years_of_experience",
        "application_status",
        "created_at",
    )

    list_filter = (
        "application_status",
        "skill_category",
        "years_of_experience",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "phone_number",
    )

    readonly_fields = ("created_at",)

    inlines = [ArtisanDocumentInline]

    ordering = ("-created_at",)

    actions = ["approve_applications", "reject_applications"]

    def approve_applications(self, request, queryset):
        queryset.update(application_status="approved")
    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        queryset.update(application_status="rejected")
    reject_applications.short_description = "Reject selected applications"


@admin.register(ArtisanDocument)
class ArtisanDocumentAdmin(admin.ModelAdmin):
    list_display = ("application", "file", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("application__name",)
    readonly_fields = ("uploaded_at",)