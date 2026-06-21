# portfolio/models.py
from django.db import models
from django.conf import settings
from jobs.models import JobRequest
from reviews.models import Review
import django.db.models as models_django

User = settings.AUTH_USER_MODEL


class WorkerPortfolio(models.Model):
    """Simple portfolio that auto-populates from completed jobs"""
    
    worker = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='portfolio',
        limit_choices_to={'role': 'worker'}
    )
    
    # Professional Info
    professional_title = models.CharField(max_length=200, blank=True, null=True, 
                                         help_text="e.g., 'Master Plumber', 'Certified Electrician'")
    bio = models.TextField(blank=True, null=True, help_text="Short professional biography")
    
    # Skills (manual addition for skills not covered by job categories)
    skills = models.TextField(blank=True, null=True, help_text="Comma-separated list of skills")
    
    # Service Details
    service_area = models.CharField(max_length=500, blank=True, null=True, 
                                   help_text="Areas you serve")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Availability
    AVAILABILITY_CHOICES = [
        ('available', 'Available for work'),
        ('limited', 'Limited availability'),
        ('busy', 'Currently busy'),
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    
    # Profile Image
    profile_image = models.ImageField(upload_to='portfolio/profile/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='portfolio/cover/', blank=True, null=True)
    
    # Social Links (optional)
    website = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    
    # Verification
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Worker Portfolio'
        verbose_name_plural = 'Worker Portfolios'
    
    def __str__(self):
        return f"{self.worker.full_name}'s Portfolio"
    
    @property
    def completed_projects(self):
        """Get all completed jobs for this worker"""
        return JobRequest.objects.filter(
            worker=self.worker, 
            status='completed'
        ).select_related('client').order_by('-updated_at', '-created_at')
    
    @property
    def completed_projects_count(self):
        return self.completed_projects.count()
    
    @property
    def average_rating(self):
        reviews = Review.objects.filter(reviewee=self.worker)
        avg = reviews.aggregate(models_django.Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    @property
    def total_reviews(self):
        return Review.objects.filter(reviewee=self.worker).count()


class PortfolioImage(models.Model):
    """Additional portfolio images (for showcasing work)"""
    
    portfolio = models.ForeignKey(
        WorkerPortfolio,
        on_delete=models.CASCADE,
        related_name='extra_images'
    )
    image = models.ImageField(upload_to='portfolio/images/')
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"Image for {self.portfolio.worker.full_name}"