"""
Webhook callback handlers for n8n integration
"""
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
import hmac
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def n8n_property_enrichment_callback(request):
    """Handle property enrichment results from n8n"""
    try:
        # Verify webhook signature
        if not verify_webhook_signature(request):
            return HttpResponseBadRequest("Invalid signature")
        
        # Parse payload
        payload = json.loads(request.body)
        property_id = payload.get('property_id')
        enrichment_data = payload.get('enrichment_data', {})
        
        if not property_id:
            return HttpResponseBadRequest("Missing property_id")
        
        # Update property with enrichment data
        from .models import Property
        from .services import EventLogger
        
        try:
            property = Property.objects.get(id=property_id)
            
            # Update enrichment fields
            property.narrative = enrichment_data.get('narrative', '')
            property.estimate = enrichment_data.get('estimate')
            property.neighborhood_avg = enrichment_data.get('neighborhood_avg')
            property.last_updated = timezone.now()
            property.source = enrichment_data.get('source', 'n8n')
            property.save()
            
            # Log the event
            EventLogger.log_event(
                company=property.company,
                user=None,
                event_type='property.enriched',
                description=f'Property enriched: {property.title}',
                metadata={
                    'property_id': str(property.id),
                    'source': property.source,
                    'estimate': property.estimate
                }
            )
            
            logger.info(f"Property {property_id} enriched successfully")
            return JsonResponse({'status': 'success'})
            
        except Property.DoesNotExist:
            logger.error(f"Property {property_id} not found")
            return HttpResponseBadRequest("Property not found")
            
    except Exception as e:
        logger.error(f"Error processing property enrichment callback: {str(e)}")
        return HttpResponseBadRequest("Internal server error")


@csrf_exempt
@require_POST
def n8n_lead_processing_callback(request):
    """Handle lead processing results from n8n"""
    try:
        # Verify webhook signature
        if not verify_webhook_signature(request):
            return HttpResponseBadRequest("Invalid signature")
        
        # Parse payload
        payload = json.loads(request.body)
        lead_id = payload.get('lead_id')
        processing_result = payload.get('processing_result', {})
        
        if not lead_id:
            return HttpResponseBadRequest("Missing lead_id")
        
        # Update lead with processing results
        from .models import Lead
        from .services import EventLogger
        
        try:
            lead = Lead.objects.get(id=lead_id)
            
            # Update lead with processing results
            lead.webhook_sent = True
            lead.webhook_last_attempt = timezone.now()
            lead.save()
            
            # Log the event
            EventLogger.log_event(
                company=lead.company,
                user=None,
                event_type='lead.processed',
                description=f'Lead processed: {lead.name}',
                metadata={
                    'lead_id': str(lead.id),
                    'processing_result': processing_result
                }
            )
            
            logger.info(f"Lead {lead_id} processed successfully")
            return JsonResponse({'status': 'success'})
            
        except Lead.DoesNotExist:
            logger.error(f"Lead {lead_id} not found")
            return HttpResponseBadRequest("Lead not found")
            
    except Exception as e:
        logger.error(f"Error processing lead callback: {str(e)}")
        return HttpResponseBadRequest("Internal server error")


def verify_webhook_signature(request):
    """Verify webhook signature for security"""
    signature = request.headers.get('X-Signature')
    timestamp = request.headers.get('X-Timestamp')
    
    if not signature or not timestamp:
        return False
    
    # Check timestamp (prevent replay attacks)
    try:
        request_time = int(timestamp)
        current_time = int(timezone.now().timestamp())
        if abs(current_time - request_time) > 300:  # 5 minutes
            return False
    except ValueError:
        return False
    
    # Verify signature
    expected_signature = hmac.new(
        settings.WEBHOOK_SIGNING_SECRET.encode('utf-8'),
        f"{timestamp}.{request.body.decode('utf-8')}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, f"sha256={expected_signature}")
