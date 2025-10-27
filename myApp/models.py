import uuid
from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    """Multi-tenant company entity for row-level security"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.URLField(blank=True)
    brand_primary_color = models.CharField(max_length=7, default='#3B82F6', help_text='Hex color code')
    brand_secondary_color = models.CharField(max_length=7, default='#1E40AF', help_text='Hex color code')
    brand_tone = models.CharField(max_length=50, default='professional', help_text='Brand personality tone')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
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
    
    # Property IQ enrichment fields
    narrative = models.TextField(blank=True, help_text='AI-generated property analysis')
    estimate = models.IntegerField(null=True, blank=True, help_text='Market value estimate')
    neighborhood_avg = models.IntegerField(null=True, blank=True, help_text='Neighborhood average price')
    last_updated = models.DateTimeField(null=True, blank=True, help_text='Last enrichment update')
    source = models.CharField(max_length=50, blank=True, help_text='Data source (rentcast, etc.)')
    
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
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
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
    
    # Lead processing fields
    autoresponder_sent = models.BooleanField(default=False)
    webhook_sent = models.BooleanField(default=False)
    webhook_attempts = models.IntegerField(default=0)
    webhook_last_attempt = models.DateTimeField(null=True, blank=True)
    
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
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
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


class OutboxMessage(models.Model):
    """DB Outbox pattern for reliable webhook delivery"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retry', 'Retry'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=50)  # lead.created, property.enrich, etc.
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    correlation_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.event_type} ({self.status})"


class EventLog(models.Model):
    """Audit trail for dashboard activity"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=50)  # property.created, lead.created, webhook.sent
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.event_type}: {self.description}"


