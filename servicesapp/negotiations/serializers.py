# negotiations/serializers.py
from rest_framework import serializers
from .models import Negotiation, NegotiationMessage
from proposals.serializers import ProposalSerializer
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from datetime import datetime


class NegotiationMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = NegotiationMessage
        fields = [
            'id', 'sender', 'sender_name', 'sender_role', 'message_type',
            'message', 'offer', 'is_system_message', 'progress_percentage',
            'milestone_note', 'images', 'uploaded_images', 'image_urls', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'sender', 'images', 'image_urls']
    
    def get_image_urls(self, obj):
        """Return absolute URLs for images - similar to ProjectImageSerializer"""
        request = self.context.get('request')
        image_urls = []
        
        if obj.images and isinstance(obj.images, list):
            for img in obj.images:
                if isinstance(img, dict):
                    # Get the URL from stored dict
                    url = img.get('url', img.get('image_url'))
                    if url:
                        # If it's a relative path, make it absolute
                        if url.startswith('/media/'):
                            if request:
                                absolute_url = request.build_absolute_uri(url)
                            else:
                                absolute_url = f"{settings.MEDIA_URL}{url.replace('/media/', '')}"
                            image_urls.append({
                                'url': absolute_url,
                                'name': img.get('name', 'image')
                            })
                        else:
                            image_urls.append({
                                'url': url,
                                'name': img.get('name', 'image')
                            })
                elif isinstance(img, str):
                    # If stored as string URL
                    if img.startswith('/media/'):
                        if request:
                            absolute_url = request.build_absolute_uri(img)
                        else:
                            absolute_url = f"{settings.MEDIA_URL}{img.replace('/media/', '')}"
                        image_urls.append({'url': absolute_url, 'name': 'image'})
                    else:
                        image_urls.append({'url': img, 'name': 'image'})
        
        return image_urls
    
    def save_uploaded_image(self, image, user_id, request=None):
        """Save uploaded image and return the URL with absolute path"""
        try:
            # Generate unique filename
            timestamp = int(datetime.now().timestamp())
            original_name = image.name
            safe_name = original_name.replace(' ', '_').replace('/', '_')
            filename = f"negotiation_messages/user_{user_id}/{timestamp}_{safe_name}"
            
            # Save the file
            saved_path = default_storage.save(filename, ContentFile(image.read()))
            
            # Build absolute URL (like ProjectImageSerializer)
            if request:
                # Build absolute URI using the request
                absolute_url = request.build_absolute_uri(default_storage.url(saved_path))
            else:
                # Fallback to media URL
                absolute_url = f"{settings.MEDIA_URL}{saved_path}"
            
            return {
                'url': absolute_url,
                'name': original_name,
                'size': image.size,
                'type': safe_name.split('.')[-1] if '.' in safe_name else 'image',
                'uploaded_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error saving image: {e}")
            return None
    
    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        request = self.context.get('request')
        
        # Handle image uploads
        if uploaded_images:
            saved_images = []
            for image in uploaded_images:
                if request and request.user:
                    image_data = self.save_uploaded_image(image, request.user.id, request)
                    if image_data:
                        saved_images.append(image_data)
            
            if saved_images:
                validated_data['images'] = saved_images
        
        return super().create(validated_data)


class NegotiationSerializer(serializers.ModelSerializer):
    messages = NegotiationMessageSerializer(many=True, read_only=True)
    proposal_details = ProposalSerializer(source='proposal', read_only=True)
    worker_name = serializers.CharField(source='proposal.worker.full_name', read_only=True)
    worker_id = serializers.IntegerField(source='proposal.worker.id', read_only=True)
    client_name = serializers.CharField(source='proposal.job.client.full_name', read_only=True)
    client_id = serializers.IntegerField(source='proposal.job.client.id', read_only=True)
    job_title = serializers.CharField(source='proposal.job.title', read_only=True)
    job_id = serializers.IntegerField(source='proposal.job.id', read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Negotiation
        fields = [
            'id', 'proposal', 'proposal_details', 'current_offer',
            'pending_final_price', 'final_price', 'is_active',
            'project_status', 'progress_percentage', 'created_at',
            'updated_at', 'messages', 'worker_name', 'worker_id',
            'client_name', 'client_id', 'job_title', 'job_id', 'unread_count'
        ]

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        if request.user.role == 'client':
            return obj.unread_count_for_client
        elif request.user.role == 'worker':
            return obj.unread_count_for_worker
        return 0


class NegotiationListSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='proposal.worker.full_name', read_only=True)
    client_name = serializers.CharField(source='proposal.job.client.full_name', read_only=True)
    job_title = serializers.CharField(source='proposal.job.title', read_only=True)
    last_message = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    project_status = serializers.CharField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Negotiation
        fields = [
            'id', 'proposal', 'job_title', 'worker_name', 'client_name',
            'current_offer', 'final_price', 'is_active', 'project_status',
            'progress_percentage', 'last_message', 'last_message_time',
            'unread_count', 'updated_at'
        ]
    
    def get_last_message(self, obj):
        last_msg = obj.messages.first()
        return last_msg.message[:100] if last_msg else None
    
    def get_last_message_time(self, obj):
        last_msg = obj.messages.first()
        return last_msg.created_at if last_msg else obj.updated_at
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        if request.user.role == 'client':
            return obj.unread_count_for_client
        elif request.user.role == 'worker':
            return obj.unread_count_for_worker
        return 0