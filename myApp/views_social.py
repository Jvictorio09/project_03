"""
Webhook endpoints for social media integrations
"""
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.conf import settings
import json
import hmac
import hashlib
from .models import Organization
from .services_social import social_media_service
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def facebook_webhook(request):
    """Facebook Messenger webhook endpoint"""
    try:
        # Handle verification
        if request.method == 'GET':
            mode = request.GET.get('hub.mode')
            token = request.GET.get('hub.verify_token')
            challenge = request.GET.get('hub.challenge')
            
            if mode == 'subscribe' and token == settings.FACEBOOK_VERIFY_TOKEN:
                return HttpResponse(challenge)
            else:
                return HttpResponse('Verification failed', status=403)
        
        # Handle messages
        data = json.loads(request.body)
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                messaging = entry.get('messaging', [])
                
                for event in messaging:
                    sender_id = event.get('sender', {}).get('id')
                    message = event.get('message', {})
                    
                    if message and sender_id:
                        message_text = message.get('text', '')
                        
                        # Find organization by page ID
                        page_id = entry.get('id')
                        organization = Organization.objects.filter(
                            attributes__facebook__page_id=page_id
                        ).first()
                        
                        if organization:
                            # Handle message
                            social_media_service.handle_facebook_message(
                                organization,
                                sender_id,
                                message_text
                            )
        
        return HttpResponse('OK')
        
    except Exception as e:
        logger.error(f"Facebook webhook error: {e}")
        return HttpResponse('Error', status=500)


@csrf_exempt
@require_POST
def instagram_webhook(request):
    """Instagram Direct webhook endpoint"""
    try:
        # Handle verification
        if request.method == 'GET':
            mode = request.GET.get('hub.mode')
            token = request.GET.get('hub.verify_token')
            challenge = request.GET.get('hub.challenge')
            
            if mode == 'subscribe' and token == settings.FACEBOOK_VERIFY_TOKEN:
                return HttpResponse(challenge)
            else:
                return HttpResponse('Verification failed', status=403)
        
        # Handle messages
        data = json.loads(request.body)
        
        if data.get('object') == 'instagram':
            for entry in data.get('entry', []):
                messaging = entry.get('messaging', [])
                
                for event in messaging:
                    sender_id = event.get('sender', {}).get('id')
                    message = event.get('message', {})
                    
                    if message and sender_id:
                        message_text = message.get('text', '')
                        
                        # Find organization by Instagram account ID
                        account_id = entry.get('id')
                        organization = Organization.objects.filter(
                            attributes__instagram__account_id=account_id
                        ).first()
                        
                        if organization:
                            # Handle message
                            social_media_service.handle_instagram_message(
                                organization,
                                sender_id,
                                message_text
                            )
        
        return HttpResponse('OK')
        
    except Exception as e:
        logger.error(f"Instagram webhook error: {e}")
        return HttpResponse('Error', status=500)


@csrf_exempt
def connect_facebook_page(request):
    """Connect Facebook page (called from frontend)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        organization = request.organization
        if not organization:
            return JsonResponse({'error': 'Organization required'}, status=403)
        
        data = json.loads(request.body)
        access_token = data.get('access_token')
        page_id = data.get('page_id')
        
        if not access_token or not page_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Connect page
        social_media_service.connect_facebook_page(organization, access_token, page_id)
        
        return JsonResponse({
            'success': True,
            'message': 'Facebook page connected successfully'
        })
        
    except Exception as e:
        logger.error(f"Error connecting Facebook page: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def connect_instagram_account(request):
    """Connect Instagram account (called from frontend)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        organization = request.organization
        if not organization:
            return JsonResponse({'error': 'Organization required'}, status=403)
        
        data = json.loads(request.body)
        access_token = data.get('access_token')
        account_id = data.get('account_id')
        
        if not access_token:
            return JsonResponse({'error': 'Missing access token'}, status=400)
        
        # Connect account
        social_media_service.connect_instagram_account(organization, access_token, account_id)
        
        return JsonResponse({
            'success': True,
            'message': 'Instagram account connected successfully'
        })
        
    except Exception as e:
        logger.error(f"Error connecting Instagram account: {e}")
        return JsonResponse({'error': str(e)}, status=500)
