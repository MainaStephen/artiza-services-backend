from django.db import models
from django.conf import settings
from jobs.models import JobRequest
from users.models import User

User = settings.AUTH_USER_MODEL


class Review(models.Model):
    RATING_CHOICES = [
        (1, '⭐ - Poor'),
        (2, '⭐⭐ - Fair'),
        (3, '⭐⭐⭐ - Good'),
        (4, '⭐⭐⭐⭐ - Very Good'),
        (5, '⭐⭐⭐⭐⭐ - Excellent'),
    ]
    
    REVIEW_TYPES = [
        ('client_to_worker', 'Client to Worker'),
        ('worker_to_client', 'Worker to Client'),
    ]
    
    # Relationships
    job = models.ForeignKey(
        JobRequest,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    reviewee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_received'
    )
    
    # Review details
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    
    # Optional fields
    communication_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    quality_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    punctuality_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    
    # Status
    is_public = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['job', 'reviewer', 'review_type']  # One review per job per reviewer type
    
    def __str__(self):
        return f"{self.reviewer.full_name} rated {self.reviewee.full_name}: {self.rating}⭐"
    
    @property
    def rating_display(self):
        return '⭐' * self.rating
    
    @property
    def average_rating(self):
        """Calculate average of all ratings"""
        ratings = [self.rating]
        if self.communication_rating:
            ratings.append(self.communication_rating)
        if self.quality_rating:
            ratings.append(self.quality_rating)
        if self.punctuality_rating:
            ratings.append(self.punctuality_rating)
        return round(sum(ratings) / len(ratings), 1)


class UserRating(models.Model):
    """Aggregated user ratings"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='rating_summary'
    )
    average_rating = models.FloatField(default=0)
    total_reviews = models.IntegerField(default=0)
    total_5_star = models.IntegerField(default=0)
    total_4_star = models.IntegerField(default=0)
    total_3_star = models.IntegerField(default=0)
    total_2_star = models.IntegerField(default=0)
    total_1_star = models.IntegerField(default=0)
    
    # Role-specific ratings
    worker_completion_rate = models.FloatField(default=0)
    client_reliability_rate = models.FloatField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.full_name} - Avg: {self.average_rating}⭐"
    
    def update_ratings(self):
        """Recalculate ratings from all reviews"""
        reviews = Review.objects.filter(reviewee=self.user, is_public=True)
        self.total_reviews = reviews.count()
        
        if self.total_reviews > 0:
            total_rating = sum(r.rating for r in reviews)
            self.average_rating = round(total_rating / self.total_reviews, 1)
            
            # Count star distribution
            self.total_5_star = reviews.filter(rating=5).count()
            self.total_4_star = reviews.filter(rating=4).count()
            self.total_3_star = reviews.filter(rating=3).count()
            self.total_2_star = reviews.filter(rating=2).count()
            self.total_1_star = reviews.filter(rating=1).count()
        
        self.save()