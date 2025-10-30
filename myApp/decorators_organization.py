"""
Organization permission decorators
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Membership


def org_member_required(roles=None):
    """
    Decorator to require organization membership with optional role restrictions
    
    Usage:
    @org_member_required()  # Any active member
    @org_member_required(['owner', 'admin'])  # Owner or admin only
    @org_member_required(['owner'])  # Owner only
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                return redirect('/login/')
            
            # Check if user has organization context
            if not hasattr(request, 'organization') or not request.organization:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': 'Organization required'}, status=403)
                messages.error(request, 'Organization access required.')
                return redirect('/onboarding')
            
            # Check membership
            membership = Membership.objects.filter(
                user=request.user,
                organization=request.organization,
                is_active=True
            ).first()
            
            if not membership:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': 'Organization access denied'}, status=403)
                messages.error(request, 'You do not have access to this organization.')
                return redirect('/onboarding')
            
            # Check role restrictions
            if roles:
                if isinstance(roles, str):
                    roles = [roles]
                
                if membership.role not in roles:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({'error': 'Insufficient permissions'}, status=403)
                    messages.error(request, 'You do not have sufficient permissions for this action.')
                    return redirect('/dashboard')
            
            # Add membership to request for convenience
            request.membership = membership
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def org_owner_required(view_func):
    """Decorator to require organization owner role"""
    return org_member_required(['owner'])(view_func)


def org_admin_required(view_func):
    """Decorator to require organization admin or owner role"""
    return org_member_required(['owner', 'admin'])(view_func)


def public_route(view_func):
    """Decorator to mark routes as public (no organization required)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Public routes don't need organization context
        return view_func(request, *args, **kwargs)
    return wrapper
