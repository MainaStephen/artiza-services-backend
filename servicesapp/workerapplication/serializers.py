# from rest_framework import serializers
# from django.conf import settings
# from .models import ArtisanApplication, ArtisanDocument


# # -------------------------
# # Document Serializer
# # -------------------------
# class ArtisanDocumentSerializer(serializers.ModelSerializer):
#     file_url = serializers.SerializerMethodField()

#     class Meta:
#         model = ArtisanDocument
#         fields = ["id", "file", "file_url", "uploaded_at"]

#     def get_file_url(self, obj):
#         request = self.context.get("request")

#         if not obj.file:
#             return None

#         if request:
#             return request.build_absolute_uri(obj.file.url)

#         return f"{settings.MEDIA_URL}{obj.file.name}"


# # -------------------------
# # Main Application Serializer
# # -------------------------
# class ArtisanApplicationSerializer(serializers.ModelSerializer):
#     documents = ArtisanDocumentSerializer(many=True, read_only=True)

#     class Meta:
#         model = ArtisanApplication
#         fields = [
#             "id",
#             "name",
#             "email",
#             "phone_number",
#             "years_of_experience",
#             "portfolio_url",
#             "bio",
#             "documents",
#             "created_at",
#             "application_status",
#         ]  
        
#         read_only_fields = ["application_status"]# In your serializers.py
        
        
        
        
        
# class ArtisanApplicationSerializer(serializers.ModelSerializer):
#     documents = ArtisanDocumentSerializer(many=True, read_only=True)

#     class Meta:
#         model = ArtisanApplication
#         fields = [
#             "id",
#             "name",
#             "email",
#             "phone_number",
#             "years_of_experience",
#             "portfolio_url",
#             "bio",
#             "documents",
#             "created_at",
#             "application_status",
#         ]  
#         # Remove read_only_fields or make it empty
#         read_only_fields = ["id", "created_at"]  # Only keep truly read-only fields

#     def validate_years_of_experience(self, value):
#         if value < 0 or value > 100:
#             raise serializers.ValidationError(
#                 "Years of experience must be between 0 and 100."
#             )
#         return value
    
    
# # Add this to your serializers.py
# class ArtisanApplicationStatusUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ArtisanApplication
#         fields = ["application_status"]
    
#     def validate_application_status(self, value):
#         if value not in ['pending', 'approved', 'rejected']:
#             raise serializers.ValidationError("Invalid status value")
#         return value





from rest_framework import serializers
from django.conf import settings

from .models import (
    ArtisanApplication,
    ArtisanDocument,
)


# ==========================================
# Document Serializer
# ==========================================
class ArtisanDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ArtisanDocument
        fields = [
            "id",
            "file",
            "file_url",
            "uploaded_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")

        if not obj.file:
            return None

        if request:
            return request.build_absolute_uri(obj.file.url)

        return f"{settings.MEDIA_URL}{obj.file.name}"


# ==========================================
# Artisan Application Serializer
# ==========================================
class ArtisanApplicationSerializer(serializers.ModelSerializer):
    documents = ArtisanDocumentSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = ArtisanApplication
        fields = [
            "id",
            "name",
            "email",
            "phone_number",
            "skill_category",
            "years_of_experience",
            "portfolio_url",
            "bio",
            "documents",
            "application_status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def validate_years_of_experience(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Years of experience must be between 0 and 100."
            )
        return value

    def validate_skill_category(self, value):
        valid_categories = [
            "plumbing",
            "electrical",
            "mechanic",
            "painting",
            "cleaning",
            "carpentry",
            "other",
        ]

        if value not in valid_categories:
            raise serializers.ValidationError(
                f"Skill category must be one of: {', '.join(valid_categories)}"
            )

        return value


# ==========================================
# Status Update Serializer (Admin Only)
# ==========================================
class ArtisanApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtisanApplication
        fields = [
            "application_status",
        ]

    def validate_application_status(self, value):
        valid_statuses = [
            "pending",
            "approved",
            "rejected",
        ]

        if value not in valid_statuses:
            raise serializers.ValidationError(
                "Invalid status value."
            )

        return value