from django.contrib import admin
from .models import Review, UserRating


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'job', 'reviewer', 'reviewee', 'rating', 'review_type', 'created_at']
    list_filter = ['rating', 'review_type', 'created_at']
    search_fields = ['job__title', 'reviewer__full_name', 'reviewee__full_name', 'comment']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'average_rating', 'total_reviews', 'updated_at']
    readonly_fields = ['updated_at']