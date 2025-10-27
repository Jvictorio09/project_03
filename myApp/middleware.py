"""
Custom middleware for multi-tenancy and authentication
"""
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.urls import reverse
from django.utils import timezone
from .services import CompanyService
from .utils.logging_config import get_company_logger, mask_pii
import uuid


class CompanyContextMiddleware:
    """Middleware to set company context on every request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set company context
        request.company = CompanyService.get_company_from_request(request)
        
        response = self.get_response(request)
        return response


class WizardGatingMiddleware:
    """Middleware to enforce wizard completion for authenticated users"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only apply to authenticated users
        if request.user.is_authenticated:
            # Check if user has completed Step 1 (company setup)
            # For now, we'll check if they have access to a company
            if not hasattr(request, 'company') or not request.company:
                # Redirect to setup if no company access
                if not request.path.startswith('/setup/') and not request.path.startswith('/logout/'):
                    return redirect('/setup/')
        
        response = self.get_response(request)
        return response


class LoginRequiredMiddleware:
    """Middleware to protect internal routes"""
    
    # Routes that require authentication
    PROTECTED_ROUTES = [
        '/dashboard',
        '/properties',
        '/leads',
        '/campaigns',
        '/analytics',
        '/chat-agent',
        '/settings',
        '/setup',
    ]
    
    # Public routes that don't require authentication
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
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if route is protected
        is_protected = any(request.path.startswith(route) for route in self.PROTECTED_ROUTES)
        is_public = any(request.path.startswith(route) for route in self.PUBLIC_ROUTES)
        
        # If route is protected and user is not authenticated, redirect to login
        if is_protected and not request.user.is_authenticated:
            return redirect('/login/')
        
        # If route is public and user is authenticated, allow access
        if is_public:
            pass  # Allow access
        
        response = self.get_response(request)
        return response


class RequestLoggingMiddleware:
    """Middleware for structured request logging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_company_logger('request')
    
    def __call__(self, request):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id
        
        # Get company context
        company_id = None
        if hasattr(request, 'company') and request.company:
            company_id = str(request.company.id)
        
        # Get user context
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = str(request.user.id)
        
        # Log request
        self.logger.info(
            f"Request: {request.method} {request.path}",
            company_id=company_id,
            user_id=user_id,
            route=request.path,
            action=request.method,
            correlation_id=correlation_id,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:100]
        )
        
        # Process request
        start_time = timezone.now()
        response = self.get_response(request)
        end_time = timezone.now()
        
        # Log response
        duration_ms = (end_time - start_time).total_seconds() * 1000
        self.logger.info(
            f"Response: {response.status_code}",
            company_id=company_id,
            user_id=user_id,
            route=request.path,
            action=request.method,
            status=response.status_code,
            correlation_id=correlation_id,
            duration_ms=round(duration_ms, 2)
        )
        
        return response
