from django.contrib import admin
from .models import Proposal

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "worker",
        "proposed_price",
        "estimated_days",
        "is_selected",
        "created_at",
    )

    list_filter = (
        "is_selected",
        "created_at",
    )

    search_fields = (
        "worker__full_name",
        "job__title",   # adjust if your JobRequest uses a different field
    )

    readonly_fields = (
        "created_at",
    )