from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class JobRequest(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    CATEGORY_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('mechanic', 'Mechanic'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('painting', 'Painting'),
        ('other', 'Other'),
    ]

    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='jobs_created'
    )

    worker = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs_taken'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    urgency = models.CharField(
        max_length=10,
        choices=URGENCY_CHOICES,
        default='medium'
    )

    location = models.CharField(max_length=255)
    
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    timeline = models.CharField(
        max_length=100,
        help_text="e.g. '2 days', '1 week'",
        null=True,
        blank=True
    )

    scheduled_date = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"
    
    # -----------------------------
    # NEGOTIATION PROGRESS PROPERTIES
    # -----------------------------
    
    @property
    def progress_percentage(self):
        """Get progress from the accepted proposal's negotiation"""
        try:
            # Get the accepted proposal for this job
            accepted_proposal = self.proposals.filter(is_selected=True).first()
            if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                return accepted_proposal.negotiation.progress_percentage
        except Exception:
            pass
        return 0
    
    @property
    def project_negotiation_status(self):
        """Get project status from the accepted proposal's negotiation"""
        try:
            accepted_proposal = self.proposals.filter(is_selected=True).first()
            if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                return accepted_proposal.negotiation.project_status
        except Exception:
            pass
        return self.status
    
    @property
    def negotiation_id(self):
        """Get negotiation ID for direct access to messages"""
        try:
            accepted_proposal = self.proposals.filter(is_selected=True).first()
            if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                return accepted_proposal.negotiation.id
        except Exception:
            pass
        return None
    
    @property
    def final_price(self):
        """Get final agreed price from negotiation"""
        try:
            accepted_proposal = self.proposals.filter(is_selected=True).first()
            if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                return accepted_proposal.negotiation.final_price
        except Exception:
            pass
        return None
    
    @property
    def is_project_in_progress(self):
        """Check if project is in progress (negotiation completed)"""
        try:
            accepted_proposal = self.proposals.filter(is_selected=True).first()
            if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                return accepted_proposal.negotiation.project_status in ['in_progress', 'completed']
        except Exception:
            pass
        return False
    
    @property
    def can_send_updates(self):
        """Check if worker can send updates (price agreed and project active)"""
        try:
            accepted_proposal = self.proposals.filter(is_selected=True).first()
            if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                negotiation = accepted_proposal.negotiation
                return negotiation.final_price is not None and negotiation.project_status in ['in_progress']
        except Exception:
            pass
        return False


class JobImage(models.Model):
    job = models.ForeignKey(
        JobRequest,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(upload_to='job_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.job.title}"