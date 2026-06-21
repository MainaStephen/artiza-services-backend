from rest_framework import serializers
from django.conf import settings
from .models import JobRequest, JobImage


# jobs/serializers.py - Add review status to JobRequestSerializer

from rest_framework import serializers
from django.conf import settings
from .models import JobRequest, JobImage
from reviews.models import Review


class JobImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = JobImage
        fields = ["id", "image", "uploaded_at", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return f"{settings.MEDIA_URL}{obj.image}"
        return None


class JobRequestSerializer(serializers.ModelSerializer):
    images = JobImageSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    worker_name = serializers.CharField(source="worker.full_name", read_only=True)
    
    # Progress fields from model properties
    progress_percentage = serializers.IntegerField(read_only=True)
    project_negotiation_status = serializers.CharField(read_only=True)
    negotiation_id = serializers.IntegerField(read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_project_in_progress = serializers.BooleanField(read_only=True)
    can_send_updates = serializers.BooleanField(read_only=True)
    
    # Review status fields
    has_client_reviewed = serializers.SerializerMethodField()
    has_worker_reviewed = serializers.SerializerMethodField()
    client_review = serializers.SerializerMethodField()
    worker_review = serializers.SerializerMethodField()

    class Meta:
        model = JobRequest
        fields = [
            "id", "client", "client_name", "worker", "worker_name",
            "title", "description", "category", "urgency", "location",
            "latitude", "longitude", "budget", "timeline", "scheduled_date",
            "status", "images", "created_at", "updated_at",
            "progress_percentage", "project_negotiation_status", "negotiation_id",
            "final_price", "is_project_in_progress", "can_send_updates",
            "has_client_reviewed", "has_worker_reviewed", "client_review", "worker_review"
        ]
    
    def get_has_client_reviewed(self, obj):
        """Check if client has reviewed the worker for this job"""
        request = self.context.get('request')
        if request and request.user == obj.client:
            return Review.objects.filter(
                job=obj, 
                reviewer=obj.client, 
                review_type='client_to_worker'
            ).exists()
        return False
    
    def get_has_worker_reviewed(self, obj):
        """Check if worker has reviewed the client for this job"""
        request = self.context.get('request')
        if request and request.user == obj.worker:
            return Review.objects.filter(
                job=obj, 
                reviewer=obj.worker, 
                review_type='worker_to_client'
            ).exists()
        return False
    
    def get_client_review(self, obj):
        """Get client's review of the worker"""
        review = Review.objects.filter(job=obj, review_type='client_to_worker').first()
        if review:
            from reviews.serializers import ReviewSerializer
            return ReviewSerializer(review, context=self.context).data
        return None
    
    def get_worker_review(self, obj):
        """Get worker's review of the client"""
        review = Review.objects.filter(job=obj, review_type='worker_to_client').first()
        if review:
            from reviews.serializers import ReviewSerializer
            return ReviewSerializer(review, context=self.context).data
        return None
# -----------------------------
# JOB REQUEST CREATE SERIALIZER
# -----------------------------
class JobRequestCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = JobRequest
        fields = [
            "title",
            "description",
            "category",
            "urgency",
            "location",
            "budget",
            "timeline",
            "scheduled_date",
            "images",
            "latitude",
            "longitude",
        ]

    def validate(self, data):
        request = self.context.get("request")

        # -----------------------------
        # ROLE VALIDATION
        # -----------------------------
        if request.user.role != "client":
            raise serializers.ValidationError(
                "Only clients can create job requests."
            )

        # -----------------------------
        # LOCATION VALIDATION
        # -----------------------------
        lat = data.get("latitude")
        lng = data.get("longitude")

        if lat is None or lng is None:
            raise serializers.ValidationError(
                "Latitude and longitude are required for job location."
            )

        # -----------------------------
        # RANGE VALIDATION
        # -----------------------------
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                "Latitude and longitude must be numbers."
            )

        if not (-90 <= lat <= 90):
            raise serializers.ValidationError(
                "Latitude must be between -90 and 90."
            )

        if not (-180 <= lng <= 180):
            raise serializers.ValidationError(
                "Longitude must be between -180 and 180."
            )

        data["latitude"] = lat
        data["longitude"] = lng

        return data

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        request = self.context.get("request")

        # 🔥 Safety: prevent client spoofing
        validated_data.pop("client", None)

        job = JobRequest.objects.create(
            client=request.user,
            **validated_data
        )

        # Create related images
        for image in images_data:
            JobImage.objects.create(job=job, image=image)

        return job


# -----------------------------
# JOB REQUEST UPDATE SERIALIZER
# -----------------------------
class JobRequestUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobRequest
        fields = [
            "title",
            "description",
            "category",
            "urgency",
            "location",
            "budget",
            "timeline",
            "scheduled_date",
            "status",
        ]

    def validate(self, data):
        request = self.context.get("request")
        job = self.instance

        # Only owner can update job
        if job.client != request.user:
            raise serializers.ValidationError(
                "You do not have permission to edit this job."
            )

        return data


# -----------------------------
# JOB REQUEST DETAIL SERIALIZER (with full negotiation data)
# -----------------------------
class JobRequestDetailSerializer(JobRequestSerializer):
    """Extended serializer with full negotiation details"""
    
    negotiation_details = serializers.SerializerMethodField()
    
    class Meta(JobRequestSerializer.Meta):
        fields = JobRequestSerializer.Meta.fields + ['negotiation_details']
    
    def get_negotiation_details(self, obj):
        """Get full negotiation details including messages"""
        try:
            accepted_proposal = obj.proposals.filter(is_selected=True).first()
            if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                from negotiations.serializers import NegotiationSerializer
                request = self.context.get('request')
                return NegotiationSerializer(
                    accepted_proposal.negotiation, 
                    context={'request': request}
                ).data
        except Exception:
            pass
        return None