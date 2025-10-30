"""
Organization middleware for multi-tenancy
"""
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.urls import reverse
from django.utils import timezone
from .models import Organization, Membership
from .utils.logging_config import get_company_logger, mask_pii
import uuid


class OrganizationContextMiddleware:
    """Middleware to set organization context on every request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set organization context
        request.organization = self.get_organization_from_request(request)
        
        response = self.get_response(request)
        return response
    
    def get_organization_from_request(self, request):
        """Resolve organization from session or subdomain"""
        if not request.user.is_authenticated:
            return None
        
        # Check session for active organization
        active_org_id = request.session.get('active_organization_id')
        if active_org_id:
            try:
                org = Organization.objects.get(id=active_org_id)
                # Verify user has access to this organization
                if Membership.objects.filter(
                    user=request.user, 
                    organization=org, 
                    is_active=True
                ).exists():
                    return org
            except Organization.DoesNotExist:
                pass
        
        # Check subdomain (e.g., hammer.katek.ai)
        host = request.get_host()
        if '.' in host and not host.startswith('www.'):
            subdomain = host.split('.')[0]
            if subdomain not in ['app', 'www', 'api']:  # Reserved subdomains
                try:
                    org = Organization.objects.get(slug=subdomain)
                    # Verify user has access to this organization
                    if Membership.objects.filter(
                        user=request.user, 
                        organization=org, 
                        is_active=True
                    ).exists():
                        # Set as active organization in session
                        request.session['active_organization_id'] = str(org.id)
                        return org
                except Organization.DoesNotExist:
                    pass
        
        # If no organization found, try to get user's first organization
        membership = Membership.objects.filter(
            user=request.user, 
            is_active=True
        ).first()
        
        if membership:
            request.session['active_organization_id'] = str(membership.organization.id)
            return membership.organization
        
        return None


class OrganizationRequiredMiddleware:
    """Middleware to enforce organization access for protected routes"""
    
    # Routes that require organization context
    PROTECTED_ROUTES = [
        '/dashboard',
        '/properties',
        '/leads',
        '/campaigns',
        '/analytics',
        '/chat-agent',
        '/settings',
        '/onboarding',
    ]
    
    # Public routes that don't require organization
    PUBLIC_ROUTES = [
        '/',
        '/list',
        '/property/',
        '/lead/submit',
        '/book',
        '/thanks',
        '/health/',
        '/login',
        '/signup',
        '/password-reset',
        '/chat/',  # Public chat URLs
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if route is protected
        is_protected = any(request.path.startswith(route) for route in self.PROTECTED_ROUTES)
        is_public = any(request.path.startswith(route) for route in self.PUBLIC_ROUTES)
        
        # If route is protected and user is authenticated but has no organization
        if is_protected and request.user.is_authenticated:
            if not hasattr(request, 'organization') or not request.organization:
                # Redirect to onboarding if no organization
                if not request.path.startswith('/onboarding'):
                    return redirect('/onboarding')
        
        response = self.get_response(request)
        return response


class OrganizationPermissionsMiddleware:
    """Middleware to check organization permissions"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add permission helpers to request
        if hasattr(request, 'organization') and request.organization:
            request.is_org_owner = self.check_role(request, 'owner')
            request.is_org_admin = self.check_role(request, ['owner', 'admin'])
            request.is_org_member = self.check_role(request, ['owner', 'admin', 'agent'])
        else:
            request.is_org_owner = False
            request.is_org_admin = False
            request.is_org_member = False
        
        response = self.get_response(request)
        return response
    
    def check_role(self, request, roles):
        """Check if user has any of the specified roles in the organization"""
        if not request.user.is_authenticated or not hasattr(request, 'organization'):
            return False
        
        if isinstance(roles, str):
            roles = [roles]
        
        return Membership.objects.filter(
            user=request.user,
            organization=request.organization,
            role__in=roles,
            is_active=True
        ).exists()
