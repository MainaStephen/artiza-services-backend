# reviews/serializers.py - Completely independent version

from rest_framework import serializers
from .models import Review, UserRating


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)
    reviewee_name = serializers.CharField(source='reviewee.full_name', read_only=True)
    reviewer_avatar = serializers.SerializerMethodField()
    reviewer_role = serializers.CharField(source='reviewer.role', read_only=True)
    reviewee_role = serializers.CharField(source='reviewee.role', read_only=True)
    rating_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'job', 'reviewer', 'reviewer_name', 'reviewer_avatar', 'reviewer_role',
            'reviewee', 'reviewee_name', 'reviewee_role', 'review_type', 'rating', 'rating_display',
            'comment', 'communication_rating', 'quality_rating', 'punctuality_rating',
            'is_public', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_reviewer_avatar(self, obj):
        name = obj.reviewer.full_name or 'User'
        return f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=2c7da0&color=fff"
    
    def get_rating_display(self, obj):
        return '⭐' * obj.rating


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'job', 'reviewee', 'review_type', 'rating', 'comment',
            'communication_rating', 'quality_rating', 'punctuality_rating'
        ]
    
    def validate(self, data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        job = data['job']
        reviewee = data['reviewee']
        review_type = data['review_type']
        
        # Check if job is completed
        if job.status != 'completed':
            raise serializers.ValidationError("You can only review completed projects.")
        
        # Check if user is authorized to review
        if review_type == 'client_to_worker':
            if request.user != job.client:
                raise serializers.ValidationError("Only the client can review the worker.")
            if reviewee != job.worker:
                raise serializers.ValidationError("Invalid reviewee for client review.")
        elif review_type == 'worker_to_client':
            if request.user != job.worker:
                raise serializers.ValidationError("Only the worker can review the client.")
            if reviewee != job.client:
                raise serializers.ValidationError("Invalid reviewee for worker review.")
        else:
            raise serializers.ValidationError("Invalid review type.")
        
        # Check if review already exists
        if Review.objects.filter(job=job, reviewer=request.user, review_type=review_type).exists():
            raise serializers.ValidationError("You have already reviewed this project.")
        
        return data


class UserRatingSerializer(serializers.ModelSerializer):
    """Simple rating serializer without UserSerializer dependency"""
    
    class Meta:
        model = UserRating
        fields = [
            'average_rating', 'total_reviews',
            'total_5_star', 'total_4_star', 'total_3_star', 
            'total_2_star', 'total_1_star',
            'worker_completion_rate', 'client_reliability_rate', 'updated_at'
        ]