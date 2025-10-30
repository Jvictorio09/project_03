"""
Celery tasks for background automation
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_email_sequences():
    """Process due email sequence steps daily"""
    from .models import Campaign, Lead
    from .services_email import email_campaign_service
    
    logger.info("Processing email sequences...")
    
    # Get all active sequence campaigns
    active_campaigns = Campaign.objects.filter(
        status='active',
        type='sequence'
    )
    
    processed_count = 0
    
    for campaign in active_campaigns:
        try:
            # Get leads that are due for next step
            leads = Lead.objects.filter(
                organization=campaign.organization,
                status__in=['new', 'contacted', 'qualified']
            )
            
            results = email_campaign_service.process_campaign_sequence_steps(campaign)
            processed_count += len(results)
            
        except Exception as e:
            logger.error(f"Error processing campaign {campaign.id}: {e}")
    
    logger.info(f"Processed {processed_count} email sequence steps")
    return processed_count


@shared_task
def process_webhook_outbox():
    """Process pending webhooks"""
    from .models import WebhookOutbox
    from .services_lead import lead_capture_service
    
    logger.info("Processing webhook outbox...")
    
    # Process pending webhooks
    lead_capture_service.process_webhook_outbox()
    
    # Retry failed webhooks
    lead_capture_service.retry_failed_webhooks()
    
    logger.info("Webhook outbox processing complete")


@shared_task
def send_lead_autoresponder(lead_id):
    """Send autoresponder email to new lead"""
    from .models import Lead
    from .services_email import email_campaign_service
    
    try:
        lead = Lead.objects.get(id=lead_id)
        
        # Find or create welcome campaign
        welcome_campaign = None
        campaigns = Campaign.objects.filter(
            organization=lead.organization,
            name__icontains='welcome',
            type='sequence'
        ).first()
        
        if campaigns:
            welcome_campaign = campaigns
        else:
            # Create default welcome sequence
            welcome_campaign = email_campaign_service.create_campaign(
                organization=lead.organization,
                name='Welcome Sequence',
                campaign_type='sequence',
                steps_data=[
                    {
                        'offset_days': 0,
                        'subject': f'Welcome to {lead.organization.name}!',
                        'body_template': f'''
Hello {{ lead.name }},

Thank you for your interest in {lead.organization.name}! We're excited to help you find your perfect property.

Based on your preferences, we'll be sending you personalized property recommendations.

Best regards,
{lead.organization.name} Team
                        '''
                    },
                    {
                        'offset_days': 3,
                        'subject': 'Here are some properties you might love',
                        'body_template': f'''
Hello {{ lead.name }},

We've found some great properties that match your criteria! Check them out:

[Property listings will be inserted here]

Have questions? Just reply to this email!

Best,
{lead.organization.name} Team
                        '''
                    }
                ]
            )
        
        # Send first step immediately
        if welcome_campaign:
            email_campaign_service.send_campaign(welcome_campaign, leads=[lead])
        
        logger.info(f"Autoresponder sent to lead {lead_id}")
        
    except Lead.DoesNotExist:
        logger.error(f"Lead {lead_id} not found")
    except Exception as e:
        logger.error(f"Error sending autoresponder to lead {lead_id}: {e}")


@shared_task
def sync_facebook_messages(organization_id):
    """Sync messages from Facebook Messenger"""
    from .models import Organization
    from .services_social import social_media_service
    
    try:
        organization = Organization.objects.get(id=organization_id)
        social_media_service.sync_facebook_messages(organization)
    except Exception as e:
        logger.error(f"Error syncing Facebook messages for org {organization_id}: {e}")


@shared_task
def sync_instagram_messages(organization_id):
    """Sync messages from Instagram Direct"""
    from .models import Organization
    from .services_social import social_media_service
    
    try:
        organization = Organization.objects.get(id=organization_id)
        social_media_service.sync_instagram_messages(organization)
    except Exception as e:
        logger.error(f"Error syncing Instagram messages for org {organization_id}: {e}")
