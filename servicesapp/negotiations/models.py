from django.db import models
from django.conf import settings
from proposals.models import Proposal

User = settings.AUTH_USER_MODEL


class Negotiation(models.Model):
    proposal = models.OneToOneField(
        Proposal,
        on_delete=models.CASCADE,
        related_name='negotiation'
    )
    current_offer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    pending_final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NEW FIELDS FOR PROJECT UPDATES
    project_status = models.CharField(
        max_length=20,
        choices=[
            ('negotiating', 'Negotiating'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='negotiating'
    )
    progress_percentage = models.PositiveIntegerField(default=0)
    
    # Notification tracking
    client_last_read = models.DateTimeField(null=True, blank=True)
    worker_last_read = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Negotiation: {self.proposal.job.title}"
    
    @property
    def unread_count_for_client(self):
        from .models import NegotiationMessage
        if self.client_last_read:
            return NegotiationMessage.objects.filter(
                negotiation=self,
                created_at__gt=self.client_last_read
            ).exclude(sender__role='client').count()
        return NegotiationMessage.objects.filter(negotiation=self).exclude(sender__role='client').count()
    
    @property
    def unread_count_for_worker(self):
        from .models import NegotiationMessage
        if self.worker_last_read:
            return NegotiationMessage.objects.filter(
                negotiation=self,
                created_at__gt=self.worker_last_read
            ).exclude(sender__role='worker').count()
        return NegotiationMessage.objects.filter(negotiation=self).exclude(sender__role='worker').count()


class NegotiationMessage(models.Model):
    MESSAGE_TYPES = [
        ('negotiation', 'Negotiation Message'),
        ('chat', 'Chat Message'),
        ('milestone', 'Milestone Update'),
        ('progress', 'Progress Update'),
    ]
    
    negotiation = models.ForeignKey(
        Negotiation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='negotiation_messages'
    )
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='negotiation')
    message = models.TextField()
    offer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_system_message = models.BooleanField(default=False)
    
    # For milestone/progress updates
    progress_percentage = models.PositiveIntegerField(null=True, blank=True)
    milestone_note = models.TextField(blank=True, null=True)
    
    # For images
    images = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.full_name}: {self.message[:50]}"