# Create a new file: multiple_gym/templatetags/dashboard_filters.py

from django import template
from decimal import Decimal
import datetime

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divides the value by the argument."""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def timeuntil_days(value):
    """Returns the number of days until the given date."""
    if not value:
        return 0
    
    if isinstance(value, datetime.datetime):
        value = value.date()
    
    today = datetime.date.today()
    if value > today:
        delta = value - today
        return delta.days
    return 0

@register.filter
def payment_status_class(status):
    """Returns Bootstrap class for payment status."""
    status_classes = {
        'paid': 'success',
        'partial': 'warning', 
        'pending': 'danger',
        'overdue': 'danger'
    }
    return status_classes.get(status, 'secondary')

@register.filter
def membership_status_class(status):
    """Returns Bootstrap class for membership status."""
    status_classes = {
        'active': 'success',
        'expired': 'danger',
        'inactive': 'warning',
        'upcoming': 'info'
    }
    return status_classes.get(status, 'secondary')

@register.filter
def days_remaining(end_date):
    """Calculate days remaining until end date."""
    if not end_date:
        return 0
    
    if isinstance(end_date, datetime.datetime):
        end_date = end_date.date()
    
    today = datetime.date.today()
    if end_date >= today:
        return (end_date - today).days
    return 0