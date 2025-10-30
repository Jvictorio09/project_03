"""
Webhook callback handlers for n8n integration and inbound email
"""
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
import hmac
import hashlib
import json
import logging
import re
import requests
from email.utils import parseaddr

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


@csrf_exempt
@require_POST
def property_enrichment_webhook(request):
    """Handle property enrichment requests from n8n"""
    try:
        # Parse payload
        payload = json.loads(request.body)
        property_id = payload.get('property_id')
        company_id = payload.get('company_id')
        
        if not property_id:
            return HttpResponseBadRequest("Missing property_id")
        
        # Get property from database
        from .models import Property
        from .services import EventLogger
        
        try:
            property = Property.objects.get(id=property_id)
            
            # Log the enrichment request
            EventLogger.log_event(
                company=property.company,
                user=None,
                event_type='property.enrichment_requested',
                description=f'Property enrichment requested: {property.title}',
                metadata={
                    'property_id': str(property.id),
                    'company_id': str(company_id) if company_id else '',
                    'payload': payload
                }
            )
            
            logger.info(f"Property enrichment webhook received for property {property_id}")
            
            # Return property data for n8n processing
            response_data = {
                'property_id': str(property.id),
                'company_id': str(property.company.id),
                'title': property.title,
                'address': property.address or '',
                'city': property.city,
                'area': property.area or '',
                'price_amount': property.price_amount,
                'beds': property.beds,
                'baths': property.baths,
                'floor_area_sqm': property.floor_area_sqm,
                'property_type': 'condo',  # Default, can be enhanced
                'description': property.description or '',
                'hero_image': property.hero_image.url if property.hero_image else '',
                'created_at': property.created_at.isoformat() if property.created_at else None
            }
            
            return JsonResponse({
                'status': 'success',
                'message': 'Property data retrieved successfully',
                'property_data': response_data
            })
            
        except Property.DoesNotExist:
            logger.error(f"Property {property_id} not found")
            return HttpResponseBadRequest("Property not found")
            
    except Exception as e:
        logger.error(f"Error processing property enrichment webhook: {str(e)}")
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


def verify_postmark_signature(request):
    """Verify Postmark inbound webhook signature"""
    signature = request.headers.get('X-Postmark-Signature')
    if not signature:
        return False
    
    secret = getattr(settings, 'POSTMARK_INBOUND_SECRET', '')
    if not secret:
        logger.warning("POSTMARK_INBOUND_SECRET not configured")
        return False
    
    # Postmark uses HMAC-SHA1 with the raw body
    body = request.body.decode('utf-8')
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha1
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@csrf_exempt
@require_POST
def n8n_send_now(request):
    """Send-now callback from n8n for campaign emails.
    Expects JSON with: message_log_id (optional for idempotency), campaign_id, step_id, lead_id, organization_id, request_id, created_at.
    Uses HMAC verification via verify_webhook_signature.
    """
    try:
        if not verify_webhook_signature(request):
            return JsonResponse({'error': 'Invalid signature'}, status=401)

        payload = json.loads(request.body or '{}')
        campaign_id = payload.get('campaign_id')
        step_id = payload.get('step_id')
        lead_id = payload.get('lead_id')
        organization_id = payload.get('organization_id')
        request_id = payload.get('request_id')

        if not (campaign_id and step_id and lead_id and organization_id and request_id):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        from .models import Campaign, CampaignStep, Lead, MessageLog, EmailAccount, Organization
        from .services_gmail import GmailService

        # Load objects
        try:
            organization = Organization.objects.get(id=organization_id)
            campaign = Campaign.objects.get(id=campaign_id, organization=organization)
            step = CampaignStep.objects.get(id=step_id, campaign=campaign)
            lead = Lead.objects.get(id=lead_id, organization=organization)
        except Exception:
            return JsonResponse({'error': 'Invalid identifiers'}, status=404)

        # Cancellation rules: paused campaign or missing consent/email
        if campaign.status in ['paused', 'completed'] or not lead.email or lead.consent_contact is False:
            # Idempotent: ensure no duplicate cancelled logs; we can just return cancelled
            return JsonResponse({'status': 'cancelled'})

        # Idempotency: if already logged as sent for this step+lead, return sent
        already_sent = MessageLog.objects.filter(campaign=campaign, campaign_step=step, lead=lead, status='sent').exists()
        if already_sent:
            return JsonResponse({'status': 'sent'})

        # Find an active email account
        email_account = EmailAccount.objects.filter(company=organization.company if hasattr(organization, 'company') else None, is_active=True).first()
        if not email_account:
            # Try fallback: any active account
            email_account = EmailAccount.objects.filter(is_active=True).first()

        if not email_account:
            # Record failure
            MessageLog.objects.create(
                organization=organization,
                campaign=campaign,
                campaign_step=step,
                lead=lead,
                status='failed',
                error_message='No active email account'
            )
            return JsonResponse({'error': 'No active email account'}, status=503)

        # Render and send via GmailService
        gmail = GmailService()
        result = gmail.send_campaign_email(
            email_account=email_account,
            lead=lead,
            campaign=campaign,
            campaign_step=step,
            template_data={}
        )

        if isinstance(result, dict) and result.get('success'):
            # Create MessageLog if not exists
            MessageLog.objects.get_or_create(
                organization=organization,
                campaign=campaign,
                campaign_step=step,
                lead=lead,
                defaults={
                    'status': 'sent',
                    'message_id': result.get('message_id', ''),
                    'provider': result.get('provider', 'gmail')
                }
            )
            return JsonResponse({'status': 'sent'})
        else:
            # Log failure (transient or permanent; n8n will retry)
            MessageLog.objects.create(
                organization=organization,
                campaign=campaign,
                campaign_step=step,
                lead=lead,
                status='failed',
                error_message=(result or {}).get('error', 'Unknown error') if isinstance(result, dict) else 'Unknown error'
            )
            return JsonResponse({'error': 'send_failed'}, status=502)

    except Exception as e:
        logger.error(f"n8n_send_now error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_POST
def n8n_fail(request):
    """Final failure notification from n8n after retries exhausted."""
    try:
        if not verify_webhook_signature(request):
            return JsonResponse({'error': 'Invalid signature'}, status=401)

        payload = json.loads(request.body or '{}')
        campaign_id = payload.get('campaign_id')
        step_id = payload.get('step_id')
        lead_id = payload.get('lead_id')
        organization_id = payload.get('organization_id')
        error_reason = payload.get('error_reason', 'Unknown')

        if not (campaign_id and step_id and lead_id and organization_id):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        from .models import Campaign, CampaignStep, Lead, MessageLog, Organization
        organization = Organization.objects.filter(id=organization_id).first()
        campaign = Campaign.objects.filter(id=campaign_id).first()
        step = CampaignStep.objects.filter(id=step_id).first()
        lead = Lead.objects.filter(id=lead_id).first()

        if not (organization and campaign and step and lead):
            return JsonResponse({'error': 'Invalid identifiers'}, status=404)

        # Mark failed (upsert)
        MessageLog.objects.update_or_create(
            organization=organization,
            campaign=campaign,
            campaign_step=step,
            lead=lead,
            defaults={
                'status': 'failed',
                'error_message': error_reason
            }
        )

        return JsonResponse({'status': 'failed_recorded'})

    except Exception as e:
        logger.error(f"n8n_fail error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
def n8n_due_messages(request):
    """Return a small list of due messages not yet sent (safety sweep).
    For MVP, we include immediate first steps (delay_hours == 0) not yet sent.
    """
    try:
        # Optional: require GET; allow POST for flexibility
        if request.method not in ['GET', 'POST']:
            return JsonResponse({'error': 'Method not allowed'}, status=405)

        # Simple selection: active campaigns with a step order=1 and delay_hours=0
        from .models import Campaign, CampaignStep, Lead, MessageLog
        due = []

        active_campaigns = Campaign.objects.filter(status='active')
        for campaign in active_campaigns:
            first_step = CampaignStep.objects.filter(campaign=campaign).order_by('order').first()
            if not first_step or (hasattr(first_step, 'delay_hours') and first_step.delay_hours > 0):
                continue
            leads = Lead.objects.filter(organization=campaign.organization, email__isnull=False).exclude(email='')
            for lead in leads[:50]:  # limit to keep response small
                already_sent = MessageLog.objects.filter(campaign=campaign, campaign_step=first_step, lead=lead, status='sent').exists()
                if not already_sent:
                    due.append({
                        'message_log_id': '',
                        'campaign_id': str(campaign.id),
                        'step_id': str(first_step.id),
                        'lead_id': str(lead.id),
                        'organization_id': str(campaign.organization.id),
                        'send_at': timezone.now().isoformat(),
                        'request_id': f"{campaign.id}:{first_step.id}:{lead.id}",
                        'created_at': timezone.now().isoformat()
                    })

        return JsonResponse({'messages': due[:100]})

    except Exception as e:
        logger.error(f"n8n_due_messages error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
def n8n_status(request):
    """Check n8n integration status"""
    try:
        use_n8n = getattr(settings, 'USE_N8N_ORCHESTRATION', False)
        n8n_webhook = getattr(settings, 'N8N_QUEUE_WEBHOOK_URL', '')
        n8n_secret = getattr(settings, 'N8N_HMAC_SECRET', '')
        
        enabled = use_n8n and n8n_webhook and n8n_secret
        
        return JsonResponse({
            'enabled': enabled,
            'use_n8n': use_n8n,
            'webhook_configured': bool(n8n_webhook),
            'secret_configured': bool(n8n_secret)
        })
        
    except Exception as e:
        logger.error(f"n8n_status error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_POST
def n8n_test(request):
    """Test n8n integration by sending a test payload"""
    try:
        use_n8n = getattr(settings, 'USE_N8N_ORCHESTRATION', False)
        n8n_webhook = getattr(settings, 'N8N_QUEUE_WEBHOOK_URL', '')
        n8n_secret = getattr(settings, 'N8N_HMAC_SECRET', '')
        
        if not (use_n8n and n8n_webhook and n8n_secret):
            return JsonResponse({
                'success': False,
                'error': 'n8n integration not configured. Set USE_N8N_ORCHESTRATION, N8N_QUEUE_WEBHOOK_URL, and N8N_HMAC_SECRET.'
            })
        
        # Create test payload
        test_payload = {
            'message_log_id': 'test-123',
            'campaign_id': 'test-campaign',
            'step_id': 'test-step',
            'lead_id': 'test-lead',
            'organization_id': 'test-org',
            'send_at': timezone.now().isoformat(),
            'request_id': 'test-request-123',
            'created_at': timezone.now().isoformat()
        }
        
        # Generate HMAC signature
        body = json.dumps(test_payload)
        ts = str(int(timezone.now().timestamp()))
        sig = hmac.new(n8n_secret.encode('utf-8'), f"{ts}.{body}".encode('utf-8'), hashlib.sha256).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-Timestamp': ts,
            'X-Signature': f"sha256={sig}"
        }
        
        # Send test request
        response = requests.post(n8n_webhook, data=body, headers=headers, timeout=10)
        
        if response.status_code in (200, 201, 202):
            return JsonResponse({
                'success': True,
                'message': f'Test payload sent successfully to n8n. Response: {response.status_code}'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'n8n webhook returned {response.status_code}: {response.text}'
            })
            
    except Exception as e:
        logger.error(f"n8n_test error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Test failed: {str(e)}'
        })

@csrf_exempt
@require_POST
def postmark_inbound(request):
    """Handle inbound email from Postmark"""
    try:
        # Verify signature
        if not verify_postmark_signature(request):
            return JsonResponse({'error': 'Invalid Postmark signature'}, status=401)
        
        # Parse Postmark payload
        payload = json.loads(request.body)
        
        # Extract email data
        from_email = payload.get('From') or payload.get('FromFull', {}).get('Email', '')
        from_name = payload.get('FromFull', {}).get('Name', '')
        subject = payload.get('Subject', '')
        text_body = payload.get('TextBody', '') or payload.get('HtmlBody', '')
        message_id = payload.get('MessageID', '')
        
        # Extract thread ID from headers
        headers = payload.get('Headers', [])
        thread_id = None
        for header in headers:
            if header.get('Name', '').lower() == 'in-reply-to':
                thread_id = header.get('Value', '')
            elif header.get('Name', '').lower() == 'references':
                thread_id = header.get('Value', '').split()[0] if header.get('Value') else None
        
        if not thread_id:
            # Use MessageID as thread identifier
            thread_id = f"email:{from_email}:{message_id}"
        
        # Find organization (by email domain or configured inbound address)
        # For now, assume first organization (in production, match by domain)
        from .models import Organization, Lead, LeadMessage, JobTask, ChannelConnection
        
        organization = Organization.objects.first()  # TODO: Match by domain
        
        if not organization:
            logger.warning("No organization found for inbound email")
            return JsonResponse({'status': 'error', 'message': 'No organization found'}, status=400)
        
        # Check channel connection status
        email_connection, _ = ChannelConnection.objects.get_or_create(
            organization=organization,
            channel='email_inbound',
            defaults={'status': 'connected'}  # Assume connected if exists
        )
        
        # Create or resolve Lead
        lead = None
        if from_email:
            # Try to find existing lead by email
            lead = Lead.objects.filter(
                organization=organization,
                email=from_email
            ).first()
        
        if not lead:
            # Create new lead
            lead = Lead.objects.create(
                organization=organization,
                name=from_name or from_email.split('@')[0],
                email=from_email,
                source='email',
                attributes={
                    'inbound_email': True,
                    'message_id': message_id
                }
            )
        
        # Create LeadMessage
        message = LeadMessage.objects.create(
            organization=organization,
            lead=lead,
            channel='email',
            external_thread_id=thread_id,
            external_msg_id=message_id,
            sender_type='human',
            text=text_body,
            raw_payload=payload
        )
        
        # Link first message to lead if needed
        if not lead.attributes.get('first_message_id'):
            lead.attributes['first_message_id'] = str(message.id)
            lead.save()
        
        # Check if we need to create email sequence job
        # This would be determined by campaign settings
        # For now, we'll create a job if lead is new
        if lead.source == 'email' and not lead.attributes.get('sequence_job_created'):
            JobTask.objects.create(
                organization=organization,
                kind='email_sequence_step',
                payload={
                    'lead_id': str(lead.id),
                    'message_id': str(message.id),
                    'step': 1
                },
                next_attempt_at=timezone.now()
            )
            lead.attributes['sequence_job_created'] = True
            lead.save()
        
        # Try to link property from message text
        from .services_lead import lead_capture_service
        lead_capture_service.link_property_for_message(message)
        
        logger.info(f"Inbound email processed: {message_id} -> Lead {lead.id}")
        
        return JsonResponse({
            'status': 'success',
            'message_id': str(message.id),
            'lead_id': str(lead.id)
        })
        
    except Exception as e:
        logger.error(f"Error processing Postmark inbound email: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
