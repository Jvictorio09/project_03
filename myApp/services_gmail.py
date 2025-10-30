"""
Gmail API service for sending emails
"""
import base64
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
from django.utils import timezone
from datetime import timedelta

from .models import EmailAccount

logger = logging.getLogger(__name__)


class GmailService:
    """Service for sending emails via Gmail API"""
    
    def __init__(self):
        self.gmail_api_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    
    def get_valid_token(self, email_account):
        """Get a valid access token, refreshing if necessary"""
        if not email_account.is_token_expired():
            return email_account.access_token
        
        # Token is expired, refresh it
        return self.refresh_access_token(email_account)
    
    def refresh_access_token(self, email_account):
        """Refresh the access token using refresh token"""
        try:
            refresh_data = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'refresh_token': email_account.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data=refresh_data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                
                # Update the email account
                email_account.access_token = new_access_token
                email_account.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
                email_account.save()
                
                logger.info(f"Refreshed access token for {email_account.email_address}")
                return new_access_token
            else:
                logger.error(f"Token refresh failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    def create_message(self, sender_email, to_email, subject, body_html, body_text=None, reply_to=None):
        """Create a MIME message for Gmail API"""
        try:
            message = MIMEMultipart('alternative')
            message['From'] = sender_email
            message['To'] = to_email
            message['Subject'] = subject
            
            if reply_to:
                message['Reply-To'] = reply_to
            
            # Add text version
            if body_text:
                text_part = MIMEText(body_text, 'plain', 'utf-8')
                message.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(body_html, 'html', 'utf-8')
            message.attach(html_part)
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            return {
                'raw': raw_message
            }
            
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None
    
    def send_email(self, email_account, to_email, subject, body_html, body_text=None, reply_to=None):
        """Send email via Gmail API"""
        try:
            # Get valid access token
            access_token = self.get_valid_token(email_account)
            if not access_token:
                logger.error(f"No valid access token for {email_account.email_address}")
                return False
            
            # Create message
            message_data = self.create_message(
                sender_email=email_account.email_address,
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                reply_to=reply_to
            )
            
            if not message_data:
                return False
            
            # Send via Gmail API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.gmail_api_url,
                headers=headers,
                json=message_data,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('id')
                
                # Update last used timestamp
                email_account.last_used_at = timezone.now()
                email_account.save()
                
                logger.info(f"Email sent successfully to {to_email}, message ID: {message_id}")
                return {
                    'success': True,
                    'message_id': message_id,
                    'provider': 'gmail'
                }
            else:
                logger.error(f"Gmail API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Gmail API error: {response.status_code}",
                    'details': response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_test_email(self, company, to_email):
        """Send a test email to verify Gmail connection"""
        try:
            email_account = EmailAccount.objects.filter(
                company=company,
                is_active=True
            ).first()
            
            if not email_account:
                logger.error("No active email account found for organization")
                return False
            
            subject = "Test Email from KaTek AI"
            body_html = f"""
            <html>
            <body>
                <h2>Gmail Connection Test</h2>
                <p>This is a test email to verify your Gmail connection is working properly.</p>
                <p>If you received this email, your Gmail account is successfully connected and ready for email campaigns!</p>
                <hr>
                <p><small>Sent from KaTek AI Real Estate Platform</small></p>
            </body>
            </html>
            """
            
            body_text = """
            Gmail Connection Test
            
            This is a test email to verify your Gmail connection is working properly.
            
            If you received this email, your Gmail account is successfully connected and ready for email campaigns!
            
            Sent from KaTek AI Real Estate Platform
            """
            
            result = self.send_email(
                email_account=email_account,
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text
            )
            
            return result.get('success', False) if isinstance(result, dict) else result
            
        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False
    
    def send_campaign_email(self, email_account, lead, campaign, campaign_step=None, template_data=None):
        """Send campaign email to a lead"""
        try:
            # Prepare template context
            context = {
                'lead': lead,
                'company': email_account.company,
                'campaign': campaign,
                'campaign_step': campaign_step,
                **(template_data or {})
            }
            
            # Get subject and body
            if campaign_step:
                subject = self.render_template(campaign_step.subject, context)
                body_html = self.render_template(campaign_step.body_template, context)
            else:
                # Fallback to campaign name
                subject = f"Message from {email_account.organization.name}"
                body_html = f"<p>Hello {lead.name},</p><p>Thank you for your interest!</p>"
            
            # Create plain text version
            body_text = self.html_to_text(body_html)
            
            # Send email
            result = self.send_email(
                email_account=email_account,
                to_email=lead.email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                reply_to=email_account.email_address
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending campaign email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def render_template(self, template_string, context):
        """Simple template rendering (replace {{ variable }} with values)"""
        try:
            result = template_string
            
            # Replace {{ lead.name }}, {{ lead.email }}, etc.
            if 'lead' in context:
                lead = context['lead']
                result = result.replace('{{ lead.name }}', getattr(lead, 'name', ''))
                result = result.replace('{{ lead.email }}', getattr(lead, 'email', ''))
                result = result.replace('{{ lead.phone }}', getattr(lead, 'phone', ''))
                result = result.replace('{{ lead.city }}', getattr(lead, 'city', ''))
            
            if 'company' in context:
                company = context['company']
                result = result.replace('{{ company.name }}', getattr(company, 'name', ''))
                result = result.replace('{{ organization.name }}', getattr(company, 'name', ''))  # Backward compatibility
            
            return result
            
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return template_string
    
    def html_to_text(self, html):
        """Convert HTML to plain text"""
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
