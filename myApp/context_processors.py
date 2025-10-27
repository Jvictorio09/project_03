"""
Context processors for global template variables
"""
from .services import FeatureFlags, CompanyService


def feature_flags(request):
    """Add feature flags to template context"""
    return {
        'feature_flags': FeatureFlags.FLAGS,
        'is_enabled': FeatureFlags.is_enabled,
        'get_disabled_tooltip': FeatureFlags.get_disabled_tooltip,
    }


def company_context(request):
    """Add company context to template context"""
    company = None
    if hasattr(request, 'user') and request.user.is_authenticated:
        company = CompanyService.get_company_from_request(request)
    
    return {
        'active_company': company,
    }
