"""
Custom OAuth adapters for organization creation
"""
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount

from .models import Organization, Membership
from .services_organization import OrganizationService


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for organization creation"""
    
    def get_login_redirect_url(self, request):
        """Redirect to onboarding or dashboard based on organization status"""
        if request.user.is_authenticated:
            # Check if user has any organizations
            user_orgs = OrganizationService.get_user_organizations(request.user)
            if user_orgs.exists():
                return '/dashboard'
            else:
                return '/onboarding'
        return '/dashboard'
    
    def get_signup_redirect_url(self, request):
        """Redirect new users to onboarding"""
        return '/onboarding'


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter for Google OAuth"""
    
    def pre_social_login(self, request, sociallogin):
        """Called before social login"""
        # This runs before the user is created or logged in
        pass
    
    def populate_user(self, request, sociallogin, data):
        """Populate user data from social account"""
        user = super().populate_user(request, sociallogin, data)
        
        # Extract organization name from email domain
        email = data.get('email', '')
        if email and '@' in email:
            domain = email.split('@')[1]
            # Create a friendly organization name
            org_name = f"{domain.split('.')[0].title()} Real Estate"
        else:
            org_name = "My Real Estate Business"
        
        # Store organization name for later use
        request.session['pending_org_name'] = org_name
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """Save user and create organization"""
        user = super().save_user(request, sociallogin, form)
        
        # Create organization for new user
        if user and not OrganizationService.get_user_organizations(user).exists():
            org_name = request.session.get('pending_org_name', f"{user.email.split('@')[0].title()} Real Estate")
            
            organization = OrganizationService.create_organization_for_user(
                user=user,
                name=org_name
            )
            
            # Set as active organization
            request.session['active_organization_id'] = str(organization.id)
            
            # Clear pending org name
            if 'pending_org_name' in request.session:
                del request.session['pending_org_name']
        
        return user
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Redirect after connecting social account"""
        return '/dashboard'
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors"""
        messages.error(request, f'Authentication failed: {error or "Unknown error"}')
        return redirect('/login/')