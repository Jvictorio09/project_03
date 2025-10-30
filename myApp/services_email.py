"""
Email campaign service
"""
import json
import requests
from django.conf import settings
from django.utils import timezone
from django.template import Template, Context
from .models import Campaign, CampaignStep, MessageLog, Lead, Organization
import logging

logger = logging.getLogger(__name__)


class EmailCampaignService:
    """Service for managing email campaigns"""
    
    def __init__(self):
        self.postmark_token = settings.POSTMARK_API_TOKEN
        self.postmark_from = settings.POSTMARK_FROM_EMAIL
    
    def create_campaign(self, organization, name, campaign_type='blast', steps_data=None):
        """Create a new email campaign"""
        campaign = Campaign.objects.create(
            organization=organization,
            name=name,
            type=campaign_type,
            status='draft'
        )
        
        # Create steps for sequence campaigns
        if campaign_type == 'sequence' and steps_data:
            for i, step_data in enumerate(steps_data):
                CampaignStep.objects.create(
                    campaign=campaign,
                    offset_days=step_data.get('offset_days', i),
                    subject=step_data.get('subject', ''),
                    body_template=step_data.get('body_template', ''),
                    order=i
                )
        
        return campaign
    
    def send_campaign(self, campaign, leads=None):
        """Send campaign to leads"""
        if campaign.type == 'blast':
            return self.send_blast_campaign(campaign, leads)
        elif campaign.type == 'sequence':
            return self.send_sequence_campaign(campaign, leads)
    
    def send_blast_campaign(self, campaign, leads=None):
        """Send blast campaign to leads"""
        if leads is None:
            leads = Lead.objects.filter(
                organization=campaign.organization,
                status__in=['new', 'contacted', 'qualified']
            )
        
        results = []
        for lead in leads:
            try:
                # Render email content
                subject = campaign.steps.first().subject if campaign.steps.exists() else "Message from " + campaign.organization.name
                body_template = campaign.steps.first().body_template if campaign.steps.exists() else "Hello {{ lead.name }}, thank you for your interest!"
                
                rendered_subject = self.render_template(subject, {'lead': lead, 'organization': campaign.organization})
                rendered_body = self.render_template(body_template, {'lead': lead, 'organization': campaign.organization})
                
                # Send email
                message_log = self.send_email(
                    organization=campaign.organization,
                    campaign=campaign,
                    lead=lead,
                    subject=rendered_subject,
                    body=rendered_body
                )
                
                results.append({
                    'lead': lead,
                    'status': 'sent',
                    'message_log': message_log
                })
                
            except Exception as e:
                logger.error(f"Error sending email to lead {lead.id}: {e}")
                results.append({
                    'lead': lead,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
    
    def send_sequence_campaign(self, campaign, leads=None):
        """Send sequence campaign to leads"""
        if leads is None:
            leads = Lead.objects.filter(
                organization=campaign.organization,
                status__in=['new', 'contacted', 'qualified']
            )
        
        results = []
        for lead in leads:
            # Calculate which step to send based on lead creation date
            days_since_creation = (timezone.now() - lead.created_at).days
            
            # Find appropriate step
            step = campaign.steps.filter(
                offset_days__lte=days_since_creation
            ).order_by('-offset_days').first()
            
            if step:
                try:
                    # Check if we've already sent this step
                    existing_log = MessageLog.objects.filter(
                        campaign=campaign,
                        campaign_step=step,
                        lead=lead
                    ).exists()
                    
                    if not existing_log:
                        # Render email content
                        rendered_subject = self.render_template(step.subject, {'lead': lead, 'organization': campaign.organization})
                        rendered_body = self.render_template(step.body_template, {'lead': lead, 'organization': campaign.organization})
                        
                        # Send email
                        message_log = self.send_email(
                            organization=campaign.organization,
                            campaign=campaign,
                            campaign_step=step,
                            lead=lead,
                            subject=rendered_subject,
                            body=rendered_body
                        )
                        
                        results.append({
                            'lead': lead,
                            'step': step,
                            'status': 'sent',
                            'message_log': message_log
                        })
                    
                except Exception as e:
                    logger.error(f"Error sending sequence email to lead {lead.id}: {e}")
                    results.append({
                        'lead': lead,
                        'step': step,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
    
    def send_email(self, organization, campaign, lead, subject, body, campaign_step=None):
        """Send email via Postmark"""
        try:
            # Prepare email data
            email_data = {
                'From': f"{organization.name} <{self.postmark_from}>",
                'To': lead.email,
                'Subject': subject,
                'HtmlBody': body,
                'TextBody': self.html_to_text(body),
                'Tag': f"campaign-{campaign.id}",
                'Metadata': {
                    'organization_id': str(organization.id),
                    'campaign_id': str(campaign.id),
                    'lead_id': str(lead.id)
                }
            }
            
            if campaign_step:
                email_data['Metadata']['campaign_step_id'] = str(campaign_step.id)
            
            # Send via Postmark
            response = requests.post(
                'https://api.postmarkapp.com/email',
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-Postmark-Server-Token': self.postmark_token
                },
                json=email_data,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Create message log
                message_log = MessageLog.objects.create(
                    organization=organization,
                    campaign=campaign,
                    campaign_step=campaign_step,
                    lead=lead,
                    status='sent',
                    provider_message_id=response_data.get('MessageID', '')
                )
                
                logger.info(f"Email sent successfully to {lead.email}")
                return message_log
                
            else:
                error_message = f"Postmark error: {response.status_code} - {response.text}"
                logger.error(error_message)
                
                # Create failed message log
                message_log = MessageLog.objects.create(
                    organization=organization,
                    campaign=campaign,
                    campaign_step=campaign_step,
                    lead=lead,
                    status='failed',
                    error_message=error_message
                )
                
                return message_log
                
        except Exception as e:
            error_message = f"Email send error: {str(e)}"
            logger.error(error_message)
            
            # Create failed message log
            message_log = MessageLog.objects.create(
                organization=organization,
                campaign=campaign,
                campaign_step=campaign_step,
                lead=lead,
                status='failed',
                error_message=error_message
            )
            
            return message_log
    
    def render_template(self, template_string, context):
        """Render Jinja template with context"""
        try:
            template = Template(template_string)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template_string
    
    def html_to_text(self, html):
        """Convert HTML to plain text (simple implementation)"""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def process_due_sequence_steps(self):
        """Process due sequence steps for all active campaigns"""
        active_campaigns = Campaign.objects.filter(
            status='active',
            type='sequence'
        )
        
        for campaign in active_campaigns:
            self.process_campaign_sequence_steps(campaign)
    
    def process_campaign_sequence_steps(self, campaign):
        """Process due sequence steps for a specific campaign"""
        # Get leads that are due for next step
        leads = Lead.objects.filter(
            organization=campaign.organization,
            status__in=['new', 'contacted', 'qualified']
        )
        
        for lead in leads:
            days_since_creation = (timezone.now() - lead.created_at).days
            
            # Find next step
            next_step = campaign.steps.filter(
                offset_days__lte=days_since_creation
            ).exclude(
                id__in=MessageLog.objects.filter(
                    campaign=campaign,
                    lead=lead
                ).values_list('campaign_step_id', flat=True)
            ).order_by('offset_days').first()
            
            if next_step:
                try:
                    # Render email content
                    rendered_subject = self.render_template(next_step.subject, {'lead': lead, 'organization': campaign.organization})
                    rendered_body = self.render_template(next_step.body_template, {'lead': lead, 'organization': campaign.organization})
                    
                    # Send email
                    self.send_email(
                        organization=campaign.organization,
                        campaign=campaign,
                        campaign_step=next_step,
                        lead=lead,
                        subject=rendered_subject,
                        body=rendered_body
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing sequence step for lead {lead.id}: {e}")
    
    def get_campaign_stats(self, campaign):
        """Get campaign statistics"""
        total_sent = MessageLog.objects.filter(campaign=campaign).count()
        total_delivered = MessageLog.objects.filter(campaign=campaign, status='delivered').count()
        total_opened = MessageLog.objects.filter(campaign=campaign, status='opened').count()
        total_clicked = MessageLog.objects.filter(campaign=campaign, status='clicked').count()
        
        return {
            'total_sent': total_sent,
            'total_delivered': total_delivered,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'delivery_rate': (total_delivered / total_sent * 100) if total_sent > 0 else 0,
            'open_rate': (total_opened / total_delivered * 100) if total_delivered > 0 else 0,
            'click_rate': (total_clicked / total_opened * 100) if total_opened > 0 else 0
        }


# Global instance
email_campaign_service = EmailCampaignService()
