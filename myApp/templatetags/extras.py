from django import template
from django.utils.safestring import mark_safe
from urllib.parse import quote

register = template.Library()


@register.filter
def peso(value):
    """Format number as Philippine Peso currency."""
    if value is None:
        return "₱0"
    return f"₱{value:,}"


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
