from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def cdateadd(value, days):
    return (datetime.now() + timedelta(days=int(days))).strftime('%Y-%m-%d')

@register.filter
def bstatus(value):
    return 'Cancel' if value >= datetime.now().date() else 'Watched'

@register.filter
def tformat(value, format):
    return value.strftime(format)