"""
Email service for autoresponder and transactional emails
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Property
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails"""
    
    @staticmethod
    def send_lead_autoresponder(lead, company):
        """Send autoresponder email to new lead"""
        try:
            # Get top 3 related properties
            related_properties = Property.objects.filter(
                company=company
            ).order_by('-created_at')[:3]
            
            # Prepare email context
            context = {
                'lead': lead,
                'company': company,
                'properties': related_properties,
                'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
            }
            
            # Render email template
            subject = f"Thank you for your interest - {company.name}"
            html_message = render_to_string('emails/lead_autoresponder.html', context)
            plain_message = render_to_string('emails/lead_autoresponder.txt', context)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[lead.email] if lead.email else [],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Mark as sent
            lead.autoresponder_sent = True
            lead.save(update_fields=['autoresponder_sent'])
            
            logger.info(f"Autoresponder sent to {lead.email} for company {company.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send autoresponder to {lead.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_property_estimate_update(property, company):
        """Send email when property estimates are updated"""
        try:
            # This would be sent to company users, not leads
            # Implementation depends on user notification preferences
            pass
        except Exception as e:
            logger.error(f"Failed to send property estimate update: {str(e)}")
            return False
    
    @staticmethod
    def send_webhook_failure_notification(company, error_message):
        """Send notification when webhook delivery fails"""
        try:
            # This would be sent to company admins
            # Implementation depends on admin notification preferences
            pass
        except Exception as e:
            logger.error(f"Failed to send webhook failure notification: {str(e)}")
            return False
