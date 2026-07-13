import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .. import services

register = template.Library()

register.filter("mask_cnpj", services.format_cnpj)


@register.simple_tag
def static_v(path):
    url = static(path)
    found = finders.find(path)
    if found:
        try:
            url = f"{url}?v={int(os.path.getmtime(found))}"
        except OSError:
            pass
    return url


@register.filter
def br_datetime(value):
    if not value:
        return ""

    dt = value
    if isinstance(value, str):
        dt = parse_datetime(value)
        if dt is None:
            return value

    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)

    return dt.strftime("%H:%M - %d/%m/%Y")


@register.filter
def event_dot_class(description):
    text = (description or "").lower()
    if "rejeitad" in text:
        return "dot-rejected"
    if "bloquead" in text:
        return "dot-blocked"
    if "aprovad" in text:
        return "dot-approved"
    if "análise" in text or "analise" in text:
        return "dot-pending"
    return ""
