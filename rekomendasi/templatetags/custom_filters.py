# rekomendasi/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Memecah string berdasarkan delimiter (default koma)."""
    if not value:
        return []
    return [v.strip() for v in value.split(delimiter)]
