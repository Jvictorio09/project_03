"""
Gmail OAuth connection for email campaigns
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import secrets
import logging
from datetime import timedelta

from .models import EmailAccount, Company

logger = logging.getLogger(__name__)


@login_required
def connect_gmail(request):
    """Initiate Gmail OAuth connection for email campaigns"""
    try:
        # Get company
        company = getattr(request, 'company', None)
        if not company:
            # Fallback: get from user's company
            company = Company.objects.filter(users=request.user).first()
        
        if not company:
            messages.error(request, 'No company found. Please contact support.')
            return redirect('settings')
        
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        request.session['email_oauth_state'] = state
        request.session['email_oauth_company_id'] = str(company.id)
        
        # Build Google OAuth URL with Gmail API scope
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        redirect_uri = request.build_absolute_uri('/email/oauth/callback/')
        
        if not client_id:
            messages.error(request, 'Google OAuth not configured. Please contact support.')
            return redirect('settings')
        
        google_oauth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=openid email profile https://www.googleapis.com/auth/gmail.send&"
            f"response_type=code&"
            f"state={state}&"
            f"access_type=offline&"  # Get refresh token
            f"prompt=consent"  # Force consent screen for refresh token
        )
        
        return redirect(google_oauth_url)
        
    except Exception as e:
        logger.error(f"Error initiating Gmail OAuth: {e}", exc_info=True)
        messages.error(request, 'Failed to connect Gmail. Please try again.')
        return redirect('settings')


@login_required
def email_oauth_callback(request):
    """Handle Gmail OAuth callback and store tokens"""
    try:
        # Get the authorization code
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            messages.error(request, f'Gmail connection failed: {error}')
            return redirect('settings')
        
        # Verify state parameter
        if not code or state != request.session.get('email_oauth_state'):
            messages.error(request, 'Invalid OAuth request. Please try again.')
            return redirect('settings')
        
        # Clear the state
        request.session.pop('email_oauth_state', None)
        company_id = request.session.pop('email_oauth_company_id', None)
        
        if not company_id:
            messages.error(request, 'Session expired. Please try again.')
            return redirect('settings')
        
        # Get company
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            messages.error(request, 'Company not found.')
            return redirect('settings')
        
        # Exchange code for access token
        token_data = {
            'client_id': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'GOOGLE_CLIENT_SECRET', ''),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': request.build_absolute_uri('/email/oauth/callback/')
        }
        
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data=token_data,
            timeout=30
        )
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text}")
            messages.error(request, 'Failed to get access token from Google.')
            return redirect('settings')
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 3600)
        
        if not access_token:
            messages.error(request, 'No access token received from Google.')
            return redirect('settings')
        
        # Get user info from Google
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=30
        )
        
        if user_info_response.status_code != 200:
            logger.error(f"User info fetch failed: {user_info_response.text}")
            messages.error(request, 'Failed to get user info from Google.')
            return redirect('settings')
        
        user_info = user_info_response.json()
        email = user_info.get('email')
        name = user_info.get('name')
        google_id = user_info.get('id')
        
        if not email:
            messages.error(request, 'No email address provided by Google.')
            return redirect('settings')
        
        # Check if this email is already connected
        existing_account = EmailAccount.objects.filter(
            company=company,
            email_address=email
        ).first()
        
        if existing_account:
            # Update existing account
            existing_account.access_token = access_token
            existing_account.refresh_token = refresh_token or existing_account.refresh_token
            existing_account.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            existing_account.google_id = google_id
            existing_account.is_verified = True
            existing_account.is_active = True
            existing_account.save()
            
            messages.success(request, f'Gmail account {email} updated successfully!')
        else:
            # Create new email account
            # If this is the first email account, make it primary
            is_primary = not EmailAccount.objects.filter(company=company).exists()
            
            email_account = EmailAccount.objects.create(
                company=company,
                user=request.user,
                email_address=email,
                display_name=name or email.split('@')[0].title(),
                access_token=access_token,
                refresh_token=refresh_token or '',
                token_expires_at=timezone.now() + timedelta(seconds=expires_in),
                google_id=google_id,
                is_primary=is_primary,
                is_verified=True,
                is_active=True
            )
            
            messages.success(request, f'Gmail account {email} connected successfully!')
        
        # Test email send to verify connection
        try:
            from .services_gmail import GmailService
            gmail_service = GmailService()
            test_result = gmail_service.send_test_email(company, email)
            
            if test_result:
                messages.success(request, 'Test email sent successfully! Check your inbox.')
            else:
                messages.warning(request, 'Gmail connected but test email failed. You can still use it for campaigns.')
        except Exception as test_error:
            logger.warning(f"Test email failed: {test_error}")
            messages.warning(request, 'Gmail connected but test email failed. You can still use it for campaigns.')
        
        return redirect('settings')
        
    except Exception as e:
        logger.error(f"Error in Gmail OAuth callback: {e}", exc_info=True)
        messages.error(request, 'Failed to connect Gmail. Please try again.')
        return redirect('settings')


@login_required
def disconnect_gmail(request, email_account_id):
    """Disconnect a Gmail account"""
    try:
        organization = getattr(request, 'organization', None)
        if not organization:
            return JsonResponse({'error': 'No organization found'}, status=400)
        
        email_account = EmailAccount.objects.get(
            id=email_account_id,
            organization=organization,
            user=request.user
        )
        
        email_address = email_account.email_address
        email_account.delete()
        
        messages.success(request, f'Gmail account {email_address} disconnected successfully!')
        return redirect('settings')
        
    except EmailAccount.DoesNotExist:
        messages.error(request, 'Email account not found.')
        return redirect('settings')
    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {e}", exc_info=True)
        messages.error(request, 'Failed to disconnect Gmail account.')
        return redirect('settings')


@login_required
def set_primary_email(request, email_account_id):
    """Set an email account as primary for the organization"""
    try:
        company = getattr(request, 'company', None)
        if not company:
            return JsonResponse({'error': 'No company found'}, status=400)
        
        email_account = EmailAccount.objects.get(
            id=email_account_id,
            company=company,
            user=request.user
        )
        
        # Remove primary from all other accounts
        EmailAccount.objects.filter(
            company=company,
            is_primary=True
        ).update(is_primary=False)
        
        # Set this one as primary
        email_account.is_primary = True
        email_account.save()
        
        messages.success(request, f'{email_account.email_address} is now your primary email account.')
        return redirect('settings')
        
    except EmailAccount.DoesNotExist:
        messages.error(request, 'Email account not found.')
        return redirect('settings')
    except Exception as e:
        logger.error(f"Error setting primary email: {e}", exc_info=True)
        messages.error(request, 'Failed to set primary email account.')
        return redirect('settings')
