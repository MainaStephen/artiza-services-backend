# users/serializers.py - Fix UserSerializer with only existing fields

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from django.contrib.auth import authenticate
from .models import User


# =========================
# 🔐 LOGIN SERIALIZER (FIXED)
# =========================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["full_name"] = user.full_name
        token["email"] = user.email
        token["skill"] = user.skill if user.skill else None
        return token

    def validate(self, attrs):
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password")

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError({
                "non_field_errors": ["Invalid email or password."]
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "non_field_errors": ["Your account is not activated yet."]
            })

        data = super().validate(attrs)

        data.update({
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_verified": user.is_verified,
            "skill": user.skill if user.skill else None,
            "phone_number": user.phone_number,
        })

        return data


# =========================
# 🧍 REGISTER SERIALIZER
# =========================
class RegisterUserSerializer(serializers.ModelSerializer):
    confirmPassword = serializers.CharField(write_only=True)
    agree_to_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = [
            "full_name",
            "phone_number",
            "email",
            "password",
            "confirmPassword",
            "role",
            "agree_to_terms",
        ]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate_agree_to_terms(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must agree to the Terms & Conditions."
            )
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm = attrs.get("confirmPassword")

        if password != confirm:
            raise serializers.ValidationError({
                "confirmPassword": "Passwords do not match."
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop("confirmPassword")
        agree_to_terms = validated_data.pop("agree_to_terms")

        user = User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
            role=validated_data.get("role", "client"),
            is_active=True,
        )

        if agree_to_terms:
            user.agree_to_terms = True
            user.terms_accepted_at = timezone.now()
            user.save()

        return user


# =========================
# 👤 USER SERIALIZER (FIXED - only use fields that exist)
# =========================
# class UserSerializer(serializers.ModelSerializer):
#     """Basic user serializer for displaying user information"""
    
#     class Meta:
#         model = User
#         fields = [
#             'id', 'email', 'full_name', 'role', 'phone_number',
#             'skill', 'profile_picture', 'latitude', 'longitude', 'address',
#             'is_verified', 'is_active', 'created_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'is_verified', 'is_active']

# users/serializers.py - Fix UserSerializer

# =========================
# 👤 USER SERIALIZER (FIXED - use date_joined instead of created_at)
# =========================
class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for displaying user information"""
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role', 'phone_number',
            'skill', 'profile_picture', 'latitude', 'longitude', 'address',
            'is_verified', 'is_active', 'date_joined', 'created_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'is_verified']

# =========================
# 👷 ADMIN CREATE WORKER SERIALIZER
# =========================
class WorkerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to create worker accounts
    """
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'skill']
    
    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value
    
    def validate_skill(self, value):
        if value and value not in ['plumbing', 'mechanic', 'electrical', 'cleaning', 'painting', 'other']:
            raise serializers.ValidationError("Invalid skill selected.")
        return value
    
    def create(self, validated_data):
        user = User.objects.create(
            full_name=validated_data['full_name'],
            email=validated_data['email'].lower(),
            phone_number=validated_data['phone_number'],
            skill=validated_data.get('skill', None),
            role='worker',
            is_active=False,
            agree_to_terms=False,
            is_verified=False,
            is_staff=False,
        )
        return user


# =========================
# 🔓 WORKER ACTIVATION SERIALIZER
# =========================
class WorkerActivationSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    agree_to_terms = serializers.BooleanField(required=True)
    skill = serializers.ChoiceField(choices=User.SKILL_CHOICES, required=False, allow_null=True)
    
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if not data['agree_to_terms']:
            raise serializers.ValidationError({"agree_to_terms": "You must agree to the Terms & Conditions."})
        
        if (data.get('latitude') is not None and data.get('longitude') is None) or \
           (data.get('latitude') is None and data.get('longitude') is not None):
            raise serializers.ValidationError({
                "location": "Both latitude and longitude are required together."
            })
        
        return data


# =========================
# 👤 USER PROFILE SERIALIZER (FIXED)
# =========================
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates"""
    
    class Meta:
        model = User
        fields = [
            'full_name', 'phone_number', 'skill', 'profile_picture',
            'latitude', 'longitude', 'address','email'
        ]
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance