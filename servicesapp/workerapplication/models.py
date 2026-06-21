from django.db import models

STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]

SKILL_CATEGORY_CHOICES = [
    ("plumbing", "Plumbing"),
    ("electrical", "Electrical"),
    ("mechanic", "Mechanic"),
    ("painting", "Painting"),
    ("cleaning", "Cleaning"),
    ("carpentry", "Carpentry"),
    ("other", "Other"),
]


class ArtisanApplication(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)

    skill_category = models.CharField(
        max_length=50,
        choices=SKILL_CATEGORY_CHOICES,
    )

    years_of_experience = models.PositiveIntegerField()

    application_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    portfolio_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.get_skill_category_display()}"
    
    

class ArtisanDocument(models.Model):
    application = models.ForeignKey(
        ArtisanApplication,
        related_name="documents",
        on_delete=models.CASCADE
    )

    file = models.FileField(upload_to="artisan_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.name} document"