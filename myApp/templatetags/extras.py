from django import template
from django.utils.safestring import mark_safe
from urllib.parse import quote
from ..services import FeatureFlags

register = template.Library()


@register.filter
def peso(value):
    """Format number as US Dollar currency."""
    if value is None:
        return "$0"
    return f"${value:,}"


@register.filter
def splitcsv(value):
    """Split comma-separated values into a list."""
    if not value:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


@register.filter
def strip(value):
    """Strip whitespace from string."""
    if value is None:
        return ""
    return str(value).strip()


@register.filter
def pluralize(value):
    """Add 's' if value is not 1."""
    if value == 1:
        return ""
    return "s"


@register.filter
def urlencode(value):
    """URL encode a string."""
    if value is None:
        return ""
    return quote(str(value))


@register.filter
def split(value, delimiter):
    """Split a string by delimiter."""
    if value is None:
        return []
    return str(value).split(delimiter)


# Feature flag template tags
@register.simple_tag
def is_feature_enabled(flag_name):
    """Check if a feature flag is enabled"""
    return FeatureFlags.is_enabled(flag_name)

@register.simple_tag
def get_disabled_tooltip(flag_name):
    """Get tooltip text for disabled features"""
    return FeatureFlags.get_disabled_tooltip(flag_name)

@register.inclusion_tag('partials/feature_button.html')
def feature_button(flag_name, button_text, button_class="btn btn-primary", disabled_class="btn btn-secondary", **kwargs):
    """Render a button that respects feature flags"""
    is_enabled = FeatureFlags.is_enabled(flag_name)
    tooltip = FeatureFlags.get_disabled_tooltip(flag_name) if not is_enabled else ""
    
    return {
        'is_enabled': is_enabled,
        'button_text': button_text,
        'button_class': button_class if is_enabled else disabled_class,
        'disabled_class': disabled_class,
        'tooltip': tooltip,
        'flag_name': flag_name,
        **kwargs
    }
