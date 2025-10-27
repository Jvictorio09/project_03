"""
Webhook service for reliable delivery to n8n
"""
import hmac
import hashlib
import time
import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for reliable webhook delivery"""
    
    @staticmethod
    def sign_payload(payload, secret):
        """Sign payload with HMAC-SHA256"""
        timestamp = str(int(time.time()))
        message = f"{timestamp}.{json.dumps(payload, sort_keys=True)}"
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'X-Signature': f"sha256={signature}",
            'X-Timestamp': timestamp,
            'X-Idempotency-Key': payload.get('idempotency_key', ''),
        }
    
    @staticmethod
    def send_webhook(webhook_url, payload, secret=None):
        """Send webhook with retry logic"""
        if not secret:
            secret = settings.WEBHOOK_SIGNING_SECRET
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'KaTek-RealEstate/1.0',
        }
        
        # Add signature if secret is provided
        if secret:
            signature_headers = WebhookService.sign_payload(payload, secret)
            headers.update(signature_headers)
        
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook sent successfully to {webhook_url}")
                return True, None
            else:
                error_msg = f"Webhook failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"Webhook timeout to {webhook_url}"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Webhook request failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def get_retry_delay(attempt):
        """Calculate retry delay with exponential backoff"""
        delays = [60, 300, 900]  # 1m, 5m, 15m
        return delays[min(attempt - 1, len(delays) - 1)]
    
    @staticmethod
    def process_outbox_messages():
        """Process pending outbox messages (called by management command)"""
        from ..models import OutboxMessage
        from django.utils import timezone
        
        # Get messages ready for retry
        now = timezone.now()
        pending_messages = OutboxMessage.objects.filter(
            status__in=['pending', 'retry'],
            next_retry_at__lte=now
        ).order_by('created_at')
        
        processed_count = 0
        
        for message in pending_messages:
            try:
                # Get webhook URL from company settings or use default
                webhook_url = getattr(message.company, 'webhook_url', None)
                if not webhook_url:
                    # Use default n8n webhook URL
                    webhook_url = f"https://your-n8n-instance.com/webhook/real-estate/{message.company.slug}"
                
                # Send webhook
                success, error = WebhookService.send_webhook(
                    webhook_url,
                    message.payload,
                    settings.WEBHOOK_SIGNING_SECRET
                )
                
                if success:
                    message.status = 'sent'
                    message.last_attempt_at = now
                    message.save()
                    processed_count += 1
                    logger.info(f"Webhook sent successfully for message {message.id}")
                else:
                    # Handle failure
                    message.attempts += 1
                    message.last_attempt_at = now
                    
                    if message.attempts >= message.max_attempts:
                        message.status = 'failed'
                        logger.error(f"Webhook failed permanently for message {message.id}: {error}")
                    else:
                        # Schedule retry
                        delay_seconds = WebhookService.get_retry_delay(message.attempts)
                        message.next_retry_at = now + timedelta(seconds=delay_seconds)
                        message.status = 'retry'
                        logger.warning(f"Webhook failed for message {message.id}, retrying in {delay_seconds}s: {error}")
                    
                    message.save()
                    
            except Exception as e:
                logger.error(f"Error processing outbox message {message.id}: {str(e)}")
                message.attempts += 1
                message.last_attempt_at = now
                message.status = 'failed' if message.attempts >= message.max_attempts else 'retry'
                message.save()
        
        return processed_count
