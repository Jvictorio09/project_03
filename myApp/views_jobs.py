"""
Jobs API endpoints for n8n integration
"""
import uuid
import hmac
import hashlib
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from .models import JobTask, JobEvent, Organization
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def verify_n8n_token(request):
    """Verify Authorization bearer token"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    
    token = auth_header.split(' ', 1)[1]
    expected_token = getattr(settings, 'N8N_TOKEN', '')
    
    if not expected_token:
        logger.warning("N8N_TOKEN not configured")
        return False
    
    return hmac.compare_digest(token, expected_token)


def verify_hmac_signature(request):
    """Verify HMAC signature for callback endpoints"""
    signature_header = request.headers.get('X-Signature', '')
    timestamp_header = request.headers.get('X-Timestamp', '')
    
    if not signature_header or not timestamp_header:
        return False
    
    # Extract hex signature
    if not signature_header.startswith('sha256='):
        return False
    
    signature_hex = signature_header[7:]
    
    # Check timestamp (prevent replay attacks)
    try:
        request_time = int(timestamp_header)
        current_time = int(timezone.now().timestamp())
        if abs(current_time - request_time) > 300:  # 5 minutes
            logger.warning(f"Timestamp mismatch: {request_time} vs {current_time}")
            return False
    except ValueError:
        return False
    
    # Verify signature
    secret = getattr(settings, 'N8N_HMAC_SECRET', '')
    if not secret:
        logger.warning("N8N_HMAC_SECRET not configured")
        return False
    
    body = request.body.decode('utf-8')
    message = f"{timestamp_header}.{body}"
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature_hex, expected_signature)


@csrf_exempt
@require_http_methods(["GET"])
def jobs_next(request):
    """GET /api/jobs/next - Poll for pending jobs"""
    if not verify_n8n_token(request):
        return JsonResponse({'error': 'Invalid or missing token'}, status=401)
    
    kind = request.GET.get('kind')
    limit = int(request.GET.get('limit', 50))
    
    if limit > 200:
        limit = 200  # Cap at 200
    
    now = timezone.now()
    
    # Build query
    query = JobTask.objects.filter(
        status='pending',
        next_attempt_at__lte=now
    )
    
    if kind:
        query = query.filter(kind=kind)
    
    # Lease jobs (set status to in_progress and assign lease_id)
    jobs_to_lease = list(query[:limit])
    
    lease_duration = timedelta(minutes=10)  # 10 minute lease TTL
    
    leased_jobs = []
    with transaction.atomic():
        for job in jobs_to_lease:
            job.status = 'in_progress'
            job.lease_id = uuid.uuid4()
            job.save()
            
            # Log event
            JobEvent.objects.create(
                job=job,
                event='leased',
                details={'lease_id': str(job.lease_id)}
            )
            
            leased_jobs.append({
                'id': str(job.id),
                'kind': job.kind,
                'payload': job.payload,
                'attempts': job.attempts,
                'lease_id': str(job.lease_id),
                'created_at': job.created_at.isoformat()
            })
    
    return JsonResponse(leased_jobs, safe=False)


@csrf_exempt
@require_http_methods(["PATCH", "POST"])
def job_update(request, job_id):
    """PATCH/POST /api/jobs/<uuid> - Update job status"""
    if not verify_n8n_token(request):
        return JsonResponse({'error': 'Invalid or missing token'}, status=401)
    
    # For POST, also verify HMAC signature
    if request.method == 'POST':
        if not verify_hmac_signature(request):
            return JsonResponse({'error': 'Invalid HMAC signature'}, status=401)
    
    try:
        job = JobTask.objects.get(id=job_id)
    except JobTask.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    lease_id = data.get('lease_id')
    if not lease_id:
        return JsonResponse({'error': 'lease_id required'}, status=400)
    
    # Verify lease_id matches
    if str(job.lease_id) != str(lease_id):
        return JsonResponse({'error': 'Lease ID mismatch'}, status=409)
    
    # Update job
    status = data.get('status')
    if status and status in ['succeeded', 'failed']:
        job.status = status
    
    if 'result' in data:
        # Store result in payload or separate field
        job.payload['result'] = data['result']
    
    if 'error' in data:
        job.payload['error'] = data['error']
    
    if 'attempts' in data:
        job.attempts = data['attempts']
    
    if 'next_attempt_at' in data:
        try:
            job.next_attempt_at = timezone.datetime.fromisoformat(data['next_attempt_at'])
        except (ValueError, TypeError):
            pass
    
    # Process job result based on job kind
    result = data.get('result')
    upload_id = None
    property_id = None
    
    if status == 'succeeded' and result:
        if job.kind == 'property_ai_enrichment':
            # Process property AI enrichment
            upload_id = job.payload.get('upload_id')
            if upload_id:
                try:
                    from .models import PropertyUpload
                    from .views_properties_import import enrich_property_with_ai, create_property_from_upload
                    
                    upload = PropertyUpload.objects.get(id=upload_id)
                    
                    # Apply enrichment results
                    if result.get('enhanced_description'):
                        if upload.description:
                            upload.description = f"{upload.description}\n\n{result['enhanced_description']}"
                        else:
                            upload.description = result['enhanced_description']
                    
                    # Store enrichment data
                    upload.ai_validation_result = {
                        **upload.ai_validation_result,
                        'ai_enrichment': result,
                        'enriched_at': timezone.now().isoformat()
                    }
                    
                    # Add features to description
                    if result.get('property_features'):
                        features_text = "\n\nFeatures:\n" + "\n".join([f"• {f}" for f in result['property_features'][:10]])
                        upload.description += features_text
                    
                    upload.save()
                    
                    # Auto-complete if critical fields present
                    if upload.title and upload.price_amount and upload.city:
                        upload.status = 'complete'
                        upload.save()
                        # Create Property
                        try:
                            property_obj = create_property_from_upload(upload)
                            property_id = str(property_obj.id)
                        except Exception as e:
                            logger.error(f"Failed to create property from upload {upload_id}: {e}")
                    
                    logger.info(f"Property enrichment completed for upload {upload_id}")
                    
                except PropertyUpload.DoesNotExist:
                    logger.error(f"PropertyUpload {upload_id} not found for job {job.id}")
        
        elif job.kind == 'property_validation_deep':
            # Process deep validation results
            upload_id = job.payload.get('upload_id')
            if upload_id:
                try:
                    from .models import PropertyUpload
                    from .views_properties_import import create_property_from_upload
                    
                    upload = PropertyUpload.objects.get(id=upload_id)
                    
                    # Update validation result
                    if result.get('validation_result'):
                        upload.ai_validation_result = {
                            **upload.ai_validation_result,
                            **result['validation_result']
                        }
                    
                    if result.get('missing_fields'):
                        upload.missing_fields = result['missing_fields']
                    
                    upload.save()
                    
                    # Check if validation complete
                    if result.get('completion_score', 0) >= 0.7 or not upload.missing_fields:
                        upload.status = 'complete'
                        upload.save()
                        # Create Property
                        try:
                            property_obj = create_property_from_upload(upload)
                            property_id = str(property_obj.id)
                        except Exception as e:
                            logger.error(f"Failed to create property from upload {upload_id}: {e}")
                    
                    logger.info(f"Deep validation completed for upload {upload_id}")
                    
                except PropertyUpload.DoesNotExist:
                    logger.error(f"PropertyUpload {upload_id} not found for job {job.id}")
    
    # Clear lease on success/failure
    if status in ['succeeded', 'failed']:
        job.lease_id = None
    
    job.save()
    
    # Log event
    event_type = 'completed' if status == 'succeeded' else 'failed'
    JobEvent.objects.create(
        job=job,
        event=event_type,
        details={
            'status': status,
            'attempts': job.attempts,
            'result': data.get('result'),
            'error': data.get('error'),
            'upload_id': upload_id,
            'property_id': property_id
        }
    )
    
    response_data = {
        'status': 'success',
        'job_id': str(job.id)
    }
    
    if upload_id:
        response_data['upload_id'] = upload_id
    if property_id:
        response_data['property_id'] = property_id
    
    return JsonResponse(response_data)

