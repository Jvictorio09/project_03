"""
Social media integration service for Facebook and Instagram
"""
import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import Organization, Lead, Event, MessageLog, LeadMessage, ChannelConnection
from .views_chat import generate_ai_response, get_or_create_lead_from_session
import logging

logger = logging.getLogger(__name__)


class SocialMediaService:
    """Service for social media integrations"""
    
    def __init__(self):
        self.fb_api_version = 'v18.0'
        self.fb_graph_url = f'https://graph.facebook.com/{self.fb_api_version}'
    
    def connect_facebook_page(self, organization, access_token, page_id):
        """Connect Facebook page to organization"""
        try:
            # Verify access token
            verify_url = f'{self.fb_graph_url}/me'
            response = requests.get(verify_url, params={
                'access_token': access_token,
                'fields': 'id,name'
            })
            
            if response.status_code != 200:
                raise Exception(f"Invalid access token: {response.text}")
            
            # Get page access token
            page_token_url = f'{self.fb_graph_url}/{page_id}'
            page_response = requests.get(page_token_url, params={
                'access_token': access_token,
                'fields': 'access_token,name,id'
            })
            
            if page_response.status_code != 200:
                raise Exception(f"Failed to get page token: {page_response.text}")
            
            page_data = page_response.json()
            
            # Store connection in organization attributes
            if not organization.attributes:
                organization.attributes = {}
            
            organization.attributes['facebook'] = {
                'page_id': page_id,
                'page_name': page_data.get('name'),
                'access_token': page_data.get('access_token'),
                'connected_at': timezone.now().isoformat()
            }
            organization.save()
            
            # Subscribe to webhooks
            self.subscribe_to_facebook_webhooks(page_id, page_data.get('access_token'))
            
            logger.info(f"Facebook page {page_id} connected to organization {organization.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting Facebook page: {e}")
            raise
    
    def subscribe_to_facebook_webhooks(self, page_id, page_token):
        """Subscribe to Facebook Messenger webhooks"""
        try:
            # Subscribe to messages
            subscribe_url = f'{self.fb_graph_url}/{page_id}/subscribed_apps'
            
            response = requests.post(subscribe_url, params={
                'access_token': page_token,
                'subscribed_fields': 'messages,messaging_postbacks,messaging_optins'
            })
            
            if response.status_code == 200:
                logger.info(f"Subscribed to Facebook webhooks for page {page_id}")
                return True
            else:
                logger.warning(f"Failed to subscribe to webhooks: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error subscribing to Facebook webhooks: {e}")
            return False
    
    def handle_facebook_message(self, organization, sender_id, message_text):
        """Handle incoming Facebook message"""
        try:
            # Get or create lead from Facebook sender
            lead = self.get_or_create_facebook_lead(organization, sender_id)
            
            # Create LeadMessage record
            thread_id = f"facebook:{sender_id}"
            LeadMessage.objects.create(
                organization=organization,
                lead=lead,
                channel='facebook',
                external_thread_id=thread_id,
                sender_type='human',
                text=message_text,
                raw_payload={
                    'sender_id': sender_id,
                    'source': 'facebook'
                }
            )
            
            # Generate AI response
            response_text = generate_ai_response(organization, message_text, lead)
            
            # Send response back to Facebook
            self.send_facebook_message(organization, sender_id, response_text)
            
            # Create bot response message
            LeadMessage.objects.create(
                organization=organization,
                lead=lead,
                channel='facebook',
                external_thread_id=thread_id,
                sender_type='bot',
                text=response_text,
                raw_payload={
                    'recipient_id': sender_id,
                    'source': 'facebook'
                }
            )
            
            # Log events
            Event.objects.create(
                organization=organization,
                kind='chat.message_user',
                meta={
                    'source': 'facebook',
                    'sender_id': sender_id,
                    'message': message_text
                }
            )
            
            Event.objects.create(
                organization=organization,
                kind='chat.message_agent',
                meta={
                    'source': 'facebook',
                    'sender_id': sender_id,
                    'response': response_text
                }
            )
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error handling Facebook message: {e}")
            return "I'm sorry, I encountered an error. Please try again."
    
    def send_facebook_message(self, organization, recipient_id, message_text):
        """Send message via Facebook Messenger"""
        try:
            fb_config = organization.attributes.get('facebook', {})
            page_token = fb_config.get('access_token')
            
            if not page_token:
                raise Exception("Facebook page not connected")
            
            send_url = f'{self.fb_graph_url}/me/messages'
            
            response = requests.post(send_url, json={
                'recipient': {'id': recipient_id},
                'message': {'text': message_text},
                'messaging_type': 'RESPONSE'
            }, params={
                'access_token': page_token
            })
            
            if response.status_code == 200:
                logger.info(f"Message sent to Facebook user {recipient_id}")
                return True
            else:
                logger.error(f"Failed to send Facebook message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Facebook message: {e}")
            return False
    
    def get_or_create_facebook_lead(self, organization, sender_id):
        """Get or create lead from Facebook sender ID"""
        try:
            # Check if lead exists with this sender ID
            lead = Lead.objects.filter(
                organization=organization,
                attributes__facebook_sender_id=sender_id
            ).first()
            
            if not lead:
                # Get sender info from Facebook
                fb_config = organization.attributes.get('facebook', {})
                page_token = fb_config.get('access_token')
                
                if page_token:
                    # Get user profile
                    profile_url = f'{self.fb_graph_url}/{sender_id}'
                    profile_response = requests.get(profile_url, params={
                        'access_token': page_token,
                        'fields': 'first_name,last_name,email'
                    })
                    
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
                        
                        if not name:
                            name = 'Facebook User'
                    else:
                        name = 'Facebook User'
                else:
                    name = 'Facebook User'
                
                # Create lead
                lead = Lead.objects.create(
                    organization=organization,
                    name=name,
                    email='',
                    phone='',
                    source='facebook',
                    attributes={
                        'facebook_sender_id': sender_id,
                        'channel': 'facebook'
                    }
                )
                
                # Queue webhook
                from .services_lead import lead_capture_service
                lead_capture_service.queue_lead_webhooks(lead)
            
            return lead
            
        except Exception as e:
            logger.error(f"Error getting/creating Facebook lead: {e}")
            # Return a temporary lead
            return Lead.objects.create(
                organization=organization,
                name='Facebook User',
                source='facebook',
                attributes={'facebook_sender_id': sender_id}
            )
    
    def sync_facebook_messages(self, organization):
        """Sync messages from Facebook (called by background task)"""
        try:
            fb_config = organization.attributes.get('facebook', {})
            if not fb_config.get('access_token'):
                return
            
            # This would typically use Facebook's webhook system
            # For now, we'll just log that sync was attempted
            logger.info(f"Syncing Facebook messages for organization {organization.name}")
            
        except Exception as e:
            logger.error(f"Error syncing Facebook messages: {e}")
    
    def connect_instagram_account(self, organization, access_token, account_id):
        """Connect Instagram account to organization"""
        try:
            # Verify access token
            verify_url = f'{self.fb_graph_url}/me'
            response = requests.get(verify_url, params={
                'access_token': access_token,
                'fields': 'id,name,instagram_business_account'
            })
            
            if response.status_code != 200:
                raise Exception(f"Invalid access token: {response.text}")
            
            user_data = response.json()
            ig_account_id = user_data.get('instagram_business_account', {}).get('id')
            
            if not ig_account_id:
                raise Exception("Instagram Business Account not found")
            
            # Store connection
            if not organization.attributes:
                organization.attributes = {}
            
            organization.attributes['instagram'] = {
                'account_id': ig_account_id,
                'access_token': access_token,
                'connected_at': timezone.now().isoformat()
            }
            organization.save()
            
            logger.info(f"Instagram account {ig_account_id} connected to organization {organization.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting Instagram account: {e}")
            raise
    
    def handle_instagram_message(self, organization, sender_id, message_text):
        """Handle incoming Instagram Direct message"""
        try:
            # Similar to Facebook handler
            lead = self.get_or_create_instagram_lead(organization, sender_id)
            
            # Create LeadMessage record
            thread_id = f"instagram:{sender_id}"
            LeadMessage.objects.create(
                organization=organization,
                lead=lead,
                channel='instagram',
                external_thread_id=thread_id,
                sender_type='human',
                text=message_text,
                raw_payload={
                    'sender_id': sender_id,
                    'source': 'instagram'
                }
            )
            
            response_text = generate_ai_response(organization, message_text, lead)
            self.send_instagram_message(organization, sender_id, response_text)
            
            # Create bot response message
            LeadMessage.objects.create(
                organization=organization,
                lead=lead,
                channel='instagram',
                external_thread_id=thread_id,
                sender_type='bot',
                text=response_text,
                raw_payload={
                    'recipient_id': sender_id,
                    'source': 'instagram'
                }
            )
            
            # Log events
            Event.objects.create(
                organization=organization,
                kind='chat.message_user',
                meta={
                    'source': 'instagram',
                    'sender_id': sender_id,
                    'message': message_text
                }
            )
            
            Event.objects.create(
                organization=organization,
                kind='chat.message_agent',
                meta={
                    'source': 'instagram',
                    'sender_id': sender_id,
                    'response': response_text
                }
            )
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error handling Instagram message: {e}")
            return "I'm sorry, I encountered an error. Please try again."
    
    def send_instagram_message(self, organization, recipient_id, message_text):
        """Send message via Instagram Direct"""
        try:
            ig_config = organization.attributes.get('instagram', {})
            account_id = ig_config.get('account_id')
            access_token = ig_config.get('access_token')
            
            if not account_id or not access_token:
                raise Exception("Instagram account not connected")
            
            # Instagram messaging API
            send_url = f'{self.fb_graph_url}/{account_id}/messages'
            
            response = requests.post(send_url, json={
                'recipient': {'id': recipient_id},
                'message': {'text': message_text}
            }, params={
                'access_token': access_token
            })
            
            if response.status_code == 200:
                logger.info(f"Message sent to Instagram user {recipient_id}")
                return True
            else:
                logger.error(f"Failed to send Instagram message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Instagram message: {e}")
            return False
    
    def get_or_create_instagram_lead(self, organization, sender_id):
        """Get or create lead from Instagram sender ID"""
        try:
            lead = Lead.objects.filter(
                organization=organization,
                attributes__instagram_sender_id=sender_id
            ).first()
            
            if not lead:
                lead = Lead.objects.create(
                    organization=organization,
                    name='Instagram User',
                    email='',
                    phone='',
                    source='instagram',
                    attributes={
                        'instagram_sender_id': sender_id,
                        'channel': 'instagram'
                    }
                )
                
                from .services_lead import lead_capture_service
                lead_capture_service.queue_lead_webhooks(lead)
            
            return lead
            
        except Exception as e:
            logger.error(f"Error getting/creating Instagram lead: {e}")
            return Lead.objects.create(
                organization=organization,
                name='Instagram User',
                source='instagram',
                attributes={'instagram_sender_id': sender_id}
            )
    
    def sync_instagram_messages(self, organization):
        """Sync messages from Instagram (called by background task)"""
        try:
            ig_config = organization.attributes.get('instagram', {})
            if not ig_config.get('access_token'):
                return
            
            logger.info(f"Syncing Instagram messages for organization {organization.name}")
            
        except Exception as e:
            logger.error(f"Error syncing Instagram messages: {e}")


# Global instance
social_media_service = SocialMediaService()
