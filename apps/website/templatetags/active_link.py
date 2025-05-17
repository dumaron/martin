from django import template
from django.urls import resolve

register = template.Library()

@register.simple_tag
def active(request, url_name, css_class='active'):
    """Returns the css_class if the current request URL matches the named URL"""
    if resolve(request.path).url_name == url_name:
        return css_class
    return ''