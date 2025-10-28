from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
import requests
import json
import secrets
import hashlib
import base64
import logging

logger = logging.getLogger(__name__)

def google_oauth_login(request):
    """Our own Google OAuth login - no allauth bullshit"""
    
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    
    # Build Google OAuth URL
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    redirect_uri = request.build_absolute_uri('/google/callback/')
    
    google_oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid email profile&"
        f"response_type=code&"
        f"state={state}"
    )
    
    return redirect(google_oauth_url)

def google_oauth_callback(request):
    """Handle Google OAuth callback"""
    
    # Get the authorization code
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    # Verify state parameter
    if not code or state != request.session.get('oauth_state'):
        messages.error(request, 'Invalid OAuth request')
        return redirect('login')
    
    # Clear the state
    request.session.pop('oauth_state', None)
    
    try:
        # Exchange code for access token
        token_data = {
            'client_id': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'GOOGLE_CLIENT_SECRET', ''),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': request.build_absolute_uri('/google/callback/')
        }
        
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data=token_data
        )
        
        if token_response.status_code != 200:
            messages.error(request, 'Failed to get access token')
            return redirect('login')
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        # Get user info from Google
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if user_info_response.status_code != 200:
            messages.error(request, 'Failed to get user info')
            return redirect('login')
        
        user_info = user_info_response.json()
        email = user_info.get('email')
        name = user_info.get('name')
        google_id = user_info.get('id')
        
        if not email:
            messages.error(request, 'No email provided by Google')
            return redirect('login')
        
        # Create or get user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': name.split(' ')[0] if name else '',
                'last_name': ' '.join(name.split(' ')[1:]) if name and len(name.split(' ')) > 1 else '',
                'is_active': True
            }
        )
        
        if created:
            messages.success(request, f'Welcome to KaTek AI, {name or email}!')
        else:
            messages.success(request, f'Welcome back, {name or email}!')
        
        # Log the user in with the correct backend
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        # Send Gmail SSO webhook for email automation
        try:
            from .webhook import send_gmail_sso_webhook
            from django.utils import timezone
            
            # Get company info (assuming user has a company)
            company = getattr(user, 'company', None)
            
            sso_data = {
                'timestamp': timezone.now().isoformat(),
                'user_id': str(user.id),
                'email': email,
                'name': name,
                'google_id': google_id,
                'access_token': access_token,
                'refresh_token': token_json.get('refresh_token', ''),
                'expires_in': token_json.get('expires_in'),
                'scope': 'openid email profile',
                'company_id': str(company.id) if company else '',
                'company_name': company.name if company else '',
                'company_slug': company.slug if company else '',
            }
            
            send_gmail_sso_webhook(sso_data)
        except Exception as webhook_error:
            # Don't fail login if webhook fails
            logger.error(f"Gmail SSO webhook failed: {str(webhook_error)}")
        
        # Redirect to dashboard
        return redirect('dashboard')
        
    except Exception as e:
        messages.error(request, f'OAuth error: {str(e)}')
        return redirect('login')

def google_oauth_error(request):
    """Handle OAuth errors"""
    error = request.GET.get('error', 'Unknown error')
    messages.error(request, f'Google OAuth error: {error}')
    return redirect('login')
