from django.contrib import admin
from .models import Negotiation, NegotiationMessage


class NegotiationMessageInline(admin.TabularInline):
    model = NegotiationMessage
    extra = 0
    readonly_fields = ('created_at',)
    fields = (
        'sender',
        'message_type',
        'message',
        'offer',
        'progress_percentage',
        'is_system_message',
        'created_at',
    )


@admin.register(Negotiation)
class NegotiationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'proposal',
        'current_offer',
        'final_price',
        'project_status',
        'progress_percentage',
        'is_active',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'is_active',
        'project_status',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'proposal__job__title',
        'proposal__worker__full_name',
        'proposal__client__full_name',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'client_last_read',
        'worker_last_read',
    )
    ordering = ('-updated_at',)
    inlines = [NegotiationMessageInline]

    fieldsets = (
        ('Proposal Info', {
            'fields': ('proposal',)
        }),
        ('Pricing', {
            'fields': (
                'current_offer',
                'final_price',
                'pending_final_price',
            )
        }),
        ('Project Status', {
            'fields': (
                'project_status',
                'progress_percentage',
                'is_active',
            )
        }),
        ('Notifications', {
            'fields': (
                'client_last_read',
                'worker_last_read',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )


@admin.register(NegotiationMessage)
class NegotiationMessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'negotiation',
        'sender',
        'message_type',
        'short_message',
        'offer',
        'is_system_message',
        'created_at',
    )
    list_filter = (
        'message_type',
        'is_system_message',
        'created_at',
    )
    search_fields = (
        'message',
        'sender__full_name',
        'negotiation__proposal__job__title',
    )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Message Info', {
            'fields': (
                'negotiation',
                'sender',
                'message_type',
                'message',
            )
        }),
        ('Offer & Progress', {
            'fields': (
                'offer',
                'progress_percentage',
                'milestone_note',
            )
        }),
        ('Media', {
            'fields': ('images',)
        }),
        ('System', {
            'fields': (
                'is_system_message',
                'created_at',
            )
        }),
    )

    def short_message(self, obj):
        return obj.message[:50]

    short_message.short_description = 'Message Preview'