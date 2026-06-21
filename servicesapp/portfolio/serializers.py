# portfolio/serializers.py
from rest_framework import serializers
from .models import WorkerPortfolio, PortfolioImage
from jobs.models import JobRequest
from reviews.models import Review  # Add this import


class PortfolioImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioImage
        fields = ['id', 'image', 'image_url', 'title', 'description', 'order', 'created_at']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class CompletedProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    client_avatar = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()
    
    class Meta:
        model = JobRequest
        fields = [
            'id', 'title', 'description', 'category', 'budget', 'final_price',
            'location', 'status', 'completed_at', 'created_at',
            'client_name', 'client_avatar', 'images', 'review'
        ]
    
    def get_client_avatar(self, obj):
        return f"https://ui-avatars.com/api/?name={obj.client.full_name}&background=2c7da0&color=fff"
    
    def get_images(self, obj):
        request = self.context.get('request')
        images = []
        for img in obj.images.all():
            if request:
                images.append(request.build_absolute_uri(img.image.url))
            else:
                images.append(img.image.url)
        return images
    
    def get_review(self, obj):
        from reviews.models import Review  # Also import here to be safe
        review = Review.objects.filter(job=obj, review_type='client_to_worker').first()
        if review:
            return {
                'rating': review.rating,
                'comment': review.comment[:200] if review.comment else '',
                'created_at': review.created_at
            }
        return None
    
    def get_final_price(self, obj):
        accepted_proposal = obj.proposals.filter(is_selected=True).first()
        if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
            if accepted_proposal.negotiation.final_price:
                return float(accepted_proposal.negotiation.final_price)
        return float(obj.budget) if obj.budget else None
    
    def get_completed_at(self, obj):
        if obj.status == 'completed':
            return obj.updated_at.strftime('%Y-%m-%d')
        return obj.created_at.strftime('%Y-%m-%d')


class WorkerPortfolioSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker.full_name', read_only=True)
    worker_joined = serializers.DateTimeField(source='worker.date_joined', read_only=True)
    profile_image_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    extra_images = PortfolioImageSerializer(many=True, read_only=True)
    completed_projects = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    completed_projects_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkerPortfolio
        fields = [
            'id', 'worker', 'worker_name', 'worker_joined',
            'professional_title', 'bio', 'skills', 'service_area',
            'hourly_rate', 'availability', 'profile_image', 'profile_image_url',
            'cover_image', 'cover_image_url', 'extra_images',
            'website', 'facebook', 'instagram',
            'completed_projects', 'completed_projects_count',
            'average_rating', 'total_reviews', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['worker', 'created_at', 'updated_at']
    
    def get_profile_image_url(self, obj):
        if obj.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None
    
    def get_cover_image_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
    
    def get_completed_projects(self, obj):
        projects = obj.completed_projects[:10]
        return CompletedProjectSerializer(projects, many=True, context=self.context).data
    
    def get_completed_projects_count(self, obj):
        return obj.completed_projects_count
    
    def get_average_rating(self, obj):
        return obj.average_rating
    
    def get_total_reviews(self, obj):
        return obj.total_reviews


class WorkerPortfolioUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating portfolio"""
    
    class Meta:
        model = WorkerPortfolio
        fields = [
            'professional_title', 'bio', 'skills', 'service_area',
            'hourly_rate', 'availability', 'profile_image', 'cover_image',
            'website', 'facebook', 'instagram'
        ]