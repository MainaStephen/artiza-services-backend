from django.contrib import admin
from .models import JobRequest, JobImage


# -----------------------------
# JOB IMAGES INLINE
# -----------------------------
class JobImageInline(admin.TabularInline):
    model = JobImage
    extra = 1
    readonly_fields = ("uploaded_at",)


# -----------------------------
# JOB REQUEST ADMIN
# -----------------------------
@admin.register(JobRequest)
class JobRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "client",
        "worker",
        "category",
        "urgency",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "category",
        "urgency",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "client__username",
        "client__email",
        "worker__username",
        "worker__email",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "client",
                "worker",
                "title",
                "description",
                "category",
                "urgency",
            )
        }),
        ("Job Details", {
            "fields": (
                "location",
                "budget",
                "timeline",
                "scheduled_date",
                "status",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
        ("Location Details", {
            "fields": (
                "longitude",
                "latitude",
                
            )
        }),
    )

    inlines = [JobImageInline]


# -----------------------------
# JOB IMAGE ADMIN (optional standalone view)
# -----------------------------
@admin.register(JobImage)
class JobImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "image",
        "uploaded_at",
    )

    list_filter = ("uploaded_at",)

    search_fields = (
        "job__title",
        "job__client__username",
    )

    readonly_fields = ("uploaded_at",)