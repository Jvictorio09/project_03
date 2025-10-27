"""
Custom decorators for authentication and wizard gating
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from .services import CompanyService


def wizard_required(view_func):
    """
    Decorator to ensure user has completed the setup wizard.
    Redirects to setup if company is not set up.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        
        # Check if user has completed Step 1 (company setup)
        company = CompanyService.get_company_from_request(request)
        if not company:
            return redirect('/setup/?step=1')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def company_required(view_func):
    """
    Decorator to ensure company context is available.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'company') or not request.company:
            # Try to get company from request
            request.company = CompanyService.get_company_from_request(request)
        
        if not request.company:
            return redirect('/setup/?step=1')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def public_route(view_func):
    """
    Decorator to mark routes as public (no authentication required).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
