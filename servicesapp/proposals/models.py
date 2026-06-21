from django.db import models
from jobs.models import JobRequest
from users.models import User

class Proposal(models.Model):
    job = models.ForeignKey(
        JobRequest,
        on_delete=models.CASCADE,
        related_name="proposals"
    )
    worker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="proposals"
    )
    proposed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    estimated_days = models.PositiveIntegerField()
    cover_letter = models.TextField()
    is_selected = models.BooleanField(default=False)  # True = accepted, False = pending/rejected
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "worker")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.worker} -> {self.job}"