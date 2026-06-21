from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


# =============================
# USER MANAGER
# =============================
class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email).lower().strip()

        user = self.model(
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        phone_number = phone_number or "0000000000"

        return self.create_user(
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            password=password,
            **extra_fields
        )


# =============================
# USER MODEL
# =============================
class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ("client", "Client"),
        ("worker", "Worker"),
        ("admin", "Admin"),
    )

    # 🔥 FIXED SKILL OPTIONS (FOR WORKERS ONLY)
    SKILL_CHOICES = (
    ("plumbing", "Plumbing"),
    ("mechanic", "Mechanic"),
    ("electrical", "Electrical"),
    ("cleaning", "Cleaning"),
    ("painting", "Painting"),
    # ("carpentry", "Carpentry"),   
    ("other", "Other"),
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15)

    # 👇 one skill for now
    skill = models.CharField(
        max_length=20,
        choices=SKILL_CHOICES,
        null=True,
        blank=True
    )

    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    agree_to_terms = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone_number"]

    def __str__(self):
        return self.full_name