import uuid
from django.db import models
from django.core import validators
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
    # Multi-tenancy
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
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
    # Multi-tenancy
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
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
    # Multi-tenancy
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
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
    # Multi-tenancy
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
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


class EmailAccount(models.Model):
    """Stores OAuth tokens for email sending via Gmail API"""
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('postmark', 'Postmark'),
        ('sendgrid', 'SendGrid'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='email_accounts', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_accounts')
    
    # Email info
    email_address = models.EmailField(help_text="Email address for sending")
    display_name = models.CharField(max_length=255, help_text="Display name for emails (e.g., 'John Doe' or 'Company Name')")
    
    # OAuth tokens (encrypted in production)
    access_token = models.TextField(help_text="Gmail API access token")
    refresh_token = models.TextField(help_text="Gmail API refresh token")
    token_expires_at = models.DateTimeField(help_text="When the access token expires")
    
    # Provider info
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='gmail')
    google_id = models.CharField(max_length=100, blank=True, help_text="Google user ID")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether this account can send emails")
    is_primary = models.BooleanField(default=False, help_text="Primary email account for company")
    is_verified = models.BooleanField(default=False, help_text="Whether the email connection is verified")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True, help_text="Last time this account was used to send emails")
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
        unique_together = ['company', 'email_address']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['company', 'is_primary']),
        ]
    
    def __str__(self) -> str:
        return f"{self.display_name} <{self.email_address}> ({self.company.name})"
    
    def is_token_expired(self) -> bool:
        """Check if access token is expired"""
        from django.utils import timezone
        return timezone.now() >= self.token_expires_at
    
    @classmethod
    def get_primary_for_company(cls, company):
        """Get primary email account for company"""
        return cls.objects.filter(
            company=company,
            is_active=True,
            is_primary=True
        ).first()


class Campaign(models.Model):
    """Email campaigns and sequences"""
    TYPE_CHOICES = [
        ('blast', 'Blast'),
        ('sequence', 'Sequence'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaigns', null=True, blank=True)
    # Multi-tenancy
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='blast')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"


class CampaignStep(models.Model):
    """Individual email steps in a campaign sequence"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=255, blank=True, help_text="Step name (e.g., 'Welcome Email')")
    subject = models.CharField(max_length=255)
    body_template = models.TextField(help_text="Email body template. Use {{ lead.name }}, {{ company.name }} for variables.")
    order = models.IntegerField(default=0, help_text="Order in sequence")
    delay_hours = models.IntegerField(default=0, help_text="Hours to wait after previous step (0 for immediate)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return f"{self.campaign.name} - Step {self.order}: {self.subject}"


class MessageLog(models.Model):
    """Tracks email sending and delivery status"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='message_logs', null=True, blank=True)
    # Multi-tenancy
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='message_logs', null=True, blank=True)
    campaign_step = models.ForeignKey(CampaignStep, on_delete=models.CASCADE, related_name='message_logs', null=True, blank=True)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='message_logs')
    email_account = models.ForeignKey(EmailAccount, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    message_id = models.CharField(max_length=255, blank=True, help_text="Provider message ID")
    provider = models.CharField(max_length=20, default='gmail', help_text="Email provider used")
    error_message = models.TextField(blank=True, help_text="Error details if failed")
    
    sent_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self) -> str:
        return f"{self.lead.email} - {self.status} - {self.campaign.name if self.campaign else 'No Campaign'}"


class HiddenProperty(models.Model):
    """Tracks properties hidden by specific users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    hidden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-hidden_at']
        unique_together = [['user', 'property']]
        indexes = [
            models.Index(fields=['user', 'property']),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} hid {self.property.title}"


class Organization(models.Model):
    """Multi-tenant organization entity"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(blank=True)
    brand_primary = models.CharField(default='#6D28D9', help_text='Primary brand color', max_length=7)
    brand_accent = models.CharField(default='#18AFAB', help_text='Accent brand color', max_length=7)
    agent_persona = models.CharField(
        choices=[('friendly_consultant', 'Friendly Consultant'), ('luxury_expert', 'Luxury Expert'), ('investor_advisor', 'Investor Advisor')],
        default='friendly_consultant',
        max_length=20
    )
    tone_formality = models.IntegerField(default=70, validators=[validators.MinValueValidator(0), validators.MaxValueValidator(100)])
    tone_warmth = models.IntegerField(default=80, validators=[validators.MinValueValidator(0), validators.MaxValueValidator(100)])
    tone_assertiveness = models.IntegerField(default=60, validators=[validators.MinValueValidator(0), validators.MaxValueValidator(100)])
    chat_greeting = models.TextField(default="Hello! I'm here to help you find your perfect property. What are you looking for today?")
    timezone = models.CharField(default='UTC', max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Organizations"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    """User membership in organizations"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('agent', 'Agent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='agent')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['user', 'organization']]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.organization.name} ({self.role})"


class Plan(models.Model):
    """Subscription plans"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    monthly_usd = models.IntegerField()
    limits = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['monthly_usd']

    def __str__(self) -> str:
        return f"{self.name} (${self.monthly_usd}/month)"


class Subscription(models.Model):
    """Organization subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trialing', 'Trialing'),
    ]
    
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('lemonsqueezy', 'LemonSqueezy'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    current_period_end = models.DateTimeField()
    customer_id = models.CharField(max_length=100, blank=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='stripe')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.organization.name} - {self.plan.name} ({self.status})"


class JobTask(models.Model):
    """Background job tasks for n8n integration"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    kind = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempts = models.IntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    lease_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'next_attempt_at']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['lease_id']),
        ]

    def __str__(self) -> str:
        return f"{self.kind} - {self.status}"


class JobEvent(models.Model):
    """Job execution events"""
    EVENT_CHOICES = [
        ('leased', 'Leased'),
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retried', 'Retried'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(JobTask, on_delete=models.CASCADE, related_name='events')
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f"{self.job.kind} - {self.event}"


class LeadMessage(models.Model):
    """Lead messages from various channels"""
    CHANNEL_CHOICES = [
        ('chat', 'Chat'),
        ('facebook', 'Facebook Messenger'),
        ('instagram', 'Instagram Direct'),
        ('email', 'Email'),
        ('webform', 'Web Form'),
    ]
    
    SENDER_CHOICES = [
        ('human', 'Human'),
        ('bot', 'Bot'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    external_thread_id = models.CharField(max_length=255)
    external_msg_id = models.CharField(max_length=255, blank=True)
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES, default='human')
    text = models.TextField()
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['organization', 'external_thread_id', 'created_at']),
            models.Index(fields=['channel', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.channel} - {self.text[:50]}..."


class ChannelConnection(models.Model):
    """Channel connection status for organizations"""
    CHANNEL_CHOICES = [
        ('facebook', 'Facebook Messenger'),
        ('instagram', 'Instagram Direct'),
        ('email_inbound', 'Inbound Email'),
        ('chat', 'Chat'),
    ]
    
    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('not_connected', 'Not Connected'),
        ('error', 'Error'),
        ('pending', 'Pending'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_connected')
    connected_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['channel']
        unique_together = [['organization', 'channel']]

    def __str__(self) -> str:
        return f"{self.organization.name} - {self.channel} ({self.status})"


class LeadPropertyLink(models.Model):
    """Links between leads and properties"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    confidence = models.FloatField(default=0.0, help_text='Confidence score 0.0-1.0')
    evidence = models.TextField(blank=True, help_text='Reason for linking')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-confidence', '-created_at']
        indexes = [
            models.Index(fields=['lead', 'property']),
            models.Index(fields=['organization', 'confidence']),
        ]

    def __str__(self) -> str:
        return f"{self.lead.name} -> {self.property.title} ({self.confidence:.2f})"


class Event(models.Model):
    """System events for analytics"""
    KIND_CHOICES = [
        ('chat.message_user', 'Chat Message User'),
        ('chat.message_agent', 'Chat Message Agent'),
        ('lead.created', 'Lead Created'),
        ('lead.qualified', 'Lead Qualified'),
        ('campaign.sent', 'Campaign Sent'),
        ('campaign.open', 'Campaign Open'),
        ('campaign.click', 'Campaign Click'),
        ('property.viewed', 'Property Viewed'),
        ('property.enriched', 'Property Enriched'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    kind = models.CharField(max_length=50, choices=KIND_CHOICES)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'kind']),
            models.Index(fields=['organization', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.kind} - {self.organization.name}"


class PropertyEmbedding(models.Model):
    """Vector embeddings for property search"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    doc_id = models.CharField(max_length=100)
    chunk = models.IntegerField()
    embedding = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['property', 'chunk']
        unique_together = [['organization', 'property', 'chunk']]
        indexes = [
            models.Index(fields=['organization', 'property']),
        ]

    def __str__(self) -> str:
        return f"{self.property.title} - Chunk {self.chunk}"


class WebhookOutbox(models.Model):
    """Outbox pattern for reliable webhook delivery"""
    TARGET_CHOICES = [
        ('n8n', 'n8n'),
        ('hubspot', 'HubSpot'),
        ('katalyst', 'Katalyst'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    target = models.CharField(max_length=20, choices=TARGET_CHOICES)
    event_kind = models.CharField(max_length=50)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.event_kind} -> {self.target} ({self.status})"


