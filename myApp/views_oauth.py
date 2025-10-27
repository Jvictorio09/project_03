from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.conf import settings

def custom_google_login(request):
    """Custom Google OAuth2 login view with our beautiful template"""
    return render(request, 'socialaccount/providers/google/login.html', {
        'provider': 'google',
        'request': request,
    })

def direct_google_oauth(request):
    """Direct redirect to Google OAuth - skip allauth's ugly page"""
    # Get the Google OAuth URL from allauth
    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView
    
    # Create the OAuth URL directly
    try:
        adapter = GoogleOAuth2Adapter(request)
        client = adapter.get_client(request)
        auth_url = client.get_authorize_url()
        return redirect(auth_url)
    except Exception as e:
        # If there's an error, fall back to allauth's URL
        return redirect('google_login')

def custom_google_callback(request):
    """Custom Google OAuth2 callback view"""
    # Redirect to allauth's actual Google OAuth flow
    return redirect('google_login')

def bypass_allauth_google_login(request):
    """Direct redirect to Google OAuth - bypass allauth templates entirely"""
    # Get the Google OAuth URL from allauth
    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView
    
    # Create the OAuth URL directly
    adapter = GoogleOAuth2Adapter(request)
    client = adapter.get_client(request)
    auth_url = client.get_authorize_url()
    
    return redirect(auth_url)

def oauth_success(request):
    """Custom OAuth success page"""
    return render(request, 'socialaccount/connections.html', {
        'user': request.user,
        'provider': 'google',
    })

def oauth_error(request):
    """Custom OAuth error page"""
    error_message = request.GET.get('error', 'An unknown error occurred')
    return render(request, 'socialaccount/authentication_error.html', {
        'error': error_message,
        'provider': 'google',
    })
