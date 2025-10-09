import uuid
from django.db import models


class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_amount = models.IntegerField()
    city = models.CharField(max_length=64)
    area = models.CharField(max_length=64, blank=True)
    beds = models.IntegerField(default=1)
    baths = models.IntegerField(default=1)
    floor_area_sqm = models.IntegerField(default=0)
    parking = models.BooleanField(default=False)
    hero_image = models.URLField(blank=True)
    badges = models.CharField(max_length=128, blank=True)
    affiliate_source = models.CharField(max_length=64, blank=True)
    commissionable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.city})"


class Lead(models.Model):
    RENT = "rent"
    BUY = "buy"
    BOR_CHOICES = [(RENT, "Rent"), (BUY, "Buy")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    buy_or_rent = models.CharField(max_length=8, choices=BOR_CHOICES)
    budget_max = models.IntegerField(null=True, blank=True)
    beds = models.IntegerField(null=True, blank=True)
    areas = models.CharField(max_length=256, blank=True)
    interest_ids = models.CharField(max_length=512, blank=True)
    utm_source = models.CharField(max_length=64, blank=True)
    utm_campaign = models.CharField(max_length=64, blank=True)
    referrer = models.URLField(blank=True)
    consent_contact = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"


class PropertyUpload(models.Model):
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('validation', 'Validation'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.OneToOneField(Property, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    
    # Initial upload data
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    price_amount = models.IntegerField(null=True, blank=True)
    city = models.CharField(max_length=64, blank=True)
    area = models.CharField(max_length=64, blank=True)
    beds = models.IntegerField(null=True, blank=True)
    baths = models.IntegerField(null=True, blank=True)
    hero_image = models.URLField(blank=True)  # Store Cloudinary URLs
    
    # AI validation data
    ai_validation_result = models.JSONField(default=dict, blank=True)
    missing_fields = models.JSONField(default=list, blank=True)
    validation_chat_history = models.JSONField(default=list, blank=True)
    consolidated_information = models.TextField(blank=True)  # Store all collected info
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Upload: {self.title or 'Untitled'} ({self.status})"


