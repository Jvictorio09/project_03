"""
Multi-tenant services for company-scoped data access
"""
from django.db import models
from django.contrib.auth.models import User
from .models import Company, Property, Lead, PropertyUpload, OutboxMessage, EventLog


class CompanyService:
    """Centralized service for company-scoped operations"""
    
    @staticmethod
    def get_company_from_request(request):
        """Get company from request context (session or URL)"""
        # Check if company is set in session (for internal admin)
        if 'active_company_id' in request.session:
            try:
                return Company.objects.get(id=request.session['active_company_id'])
            except Company.DoesNotExist:
                pass
        
        # Check if company slug is in URL path (for public routes)
        # This would be handled by URL patterns like /c/<company-slug>/
        # For now, return default company
        return CompanyService.get_default_company()
    
    @staticmethod
    def get_default_company():
        """Get or create the default demo company"""
        company, created = Company.objects.get_or_create(
            slug='demo-company',
            defaults={
                'name': 'Default Demo Company',
                'brand_primary_color': '#3B82F6',
                'brand_secondary_color': '#1E40AF',
                'brand_tone': 'professional'
            }
        )
        return company
    
    @staticmethod
    def set_active_company(request, company):
        """Set active company in session"""
        request.session['active_company_id'] = str(company.id)
    
    @staticmethod
    def get_company_scoped_queryset(model_class, company):
        """Get company-scoped queryset for any model"""
        if hasattr(model_class, 'company'):
            return model_class.objects.filter(company=company)
        return model_class.objects.all()
    
    @staticmethod
    def create_with_company(model_class, company, **kwargs):
        """Create model instance with company assignment"""
        kwargs['company'] = company
        return model_class.objects.create(**kwargs)


class FeatureFlags:
    """Feature flag system for gradual rollouts"""
    
    # Single source of truth for feature flags
    FLAGS = {
        'property_creation': True,
        'property_iq_enrichment': False,
        'lead_autoresponder': True,
        'webhook_integration': True,
        'bulk_actions': False,
        'advanced_analytics': False,
        'chat_widget': True,
        'ai_validation': True,
        'property_estimates': False,
        'lead_crud': False,
        'campaign_management': False,
        # Product feature flags
        'property_iq': True,
        'lead_robot': True,
        'ai_concierge': False,
    }
    
    @classmethod
    def is_enabled(cls, flag_name):
        """Check if a feature flag is enabled"""
        return cls.FLAGS.get(flag_name, False)
    
    @classmethod
    def get_disabled_tooltip(cls, flag_name):
        """Get tooltip text for disabled features"""
        tooltips = {
            'property_iq_enrichment': 'Property IQ coming soon—enabled in staging',
            'bulk_actions': 'Bulk actions coming soon—enabled in staging',
            'advanced_analytics': 'Advanced analytics coming soon—enabled in staging',
            'property_estimates': 'Property estimates coming soon—enabled in staging',
            'lead_crud': 'Lead management coming soon—enabled in staging',
            'campaign_management': 'Campaign management coming soon—enabled in staging',
        }
        return tooltips.get(flag_name, 'Coming soon—enabled in staging')


class EventLogger:
    """Centralized event logging for audit trail"""
    
    @staticmethod
    def log_event(company, user, event_type, description, metadata=None):
        """Log an event to the audit trail"""
        return EventLog.objects.create(
            company=company,
            user=user,
            event_type=event_type,
            description=description,
            metadata=metadata or {}
        )
    
    @staticmethod
    def get_recent_events(company, limit=5):
        """Get recent events for dashboard"""
        return EventLog.objects.filter(company=company)[:limit]


class OutboxService:
    """Service for reliable webhook delivery using DB outbox pattern"""
    
    @staticmethod
    def create_message(company, event_type, payload, correlation_id=None):
        """Create an outbox message for webhook delivery"""
        return OutboxMessage.objects.create(
            company=company,
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id or f"{event_type}_{company.id}"
        )
    
    @staticmethod
    def get_pending_messages(company=None):
        """Get pending outbox messages"""
        queryset = OutboxMessage.objects.filter(status='pending')
        if company:
            queryset = queryset.filter(company=company)
        return queryset.order_by('created_at')
    
    @staticmethod
    def mark_sent(message, success=True):
        """Mark outbox message as sent or failed"""
        if success:
            message.status = 'sent'
        else:
            message.attempts += 1
            if message.attempts >= message.max_attempts:
                message.status = 'failed'
            else:
                message.status = 'retry'
        message.save()


class LeadService:
    """Service for lead management and deduplication"""
    
    @staticmethod
    def check_duplicate(company, email=None, phone=None, property_id=None):
        """Check for duplicate leads within 24 hours"""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        queryset = Lead.objects.filter(
            company=company,
            created_at__gte=cutoff_time
        )
        
        if email:
            queryset = queryset.filter(email=email)
        elif phone:
            queryset = queryset.filter(phone=phone)
        
        if property_id:
            queryset = queryset.filter(interest_ids__contains=property_id)
        
        return queryset.exists()
    
    @staticmethod
    def create_lead(company, **kwargs):
        """Create lead with deduplication check"""
        # Check for duplicates
        if LeadService.check_duplicate(
            company=company,
            email=kwargs.get('email'),
            phone=kwargs.get('phone'),
            property_id=kwargs.get('interest_ids')
        ):
            return None, "We've already received your inquiry. Thank you!"
        
        # Create the lead
        lead = CompanyService.create_with_company(Lead, company, **kwargs)
        
        # Log the event
        EventLogger.log_event(
            company=company,
            user=None,
            event_type='lead.created',
            description=f'New lead: {lead.name}',
            metadata={'lead_id': str(lead.id)}
        )
        
        # Send autoresponder if email is provided
        if lead.email and FeatureFlags.is_enabled('lead_autoresponder'):
            from .utils.email_service import EmailService
            EmailService.send_lead_autoresponder(lead, company)
        
        # Create outbox message for webhook
        OutboxService.create_message(
            company=company,
            event_type='lead.created',
            payload={
                'lead_id': str(lead.id),
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'buy_or_rent': lead.buy_or_rent,
                'budget_max': lead.budget_max,
                'areas': lead.areas,
                'utm_source': lead.utm_source,
                'utm_campaign': lead.utm_campaign,
            }
        )
        
        return lead, None
