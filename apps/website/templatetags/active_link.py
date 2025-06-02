from django import template
from django.urls import resolve, reverse

register = template.Library()

@register.simple_tag
def active(request, url_name, css_class='active', **kwargs):
    """
    Returns the css_class if the current request URL matches the named URL.
    If kwargs are provided, it also checks that the URL parameters match.
    """
    # Normalize paths by removing trailing slashes
    current_path = request.path

    # Check if the URL name matches
    resolved = resolve(current_path)
    if resolved.url_name == url_name:
        # If there are kwargs, check if the URL parameters match
        if kwargs:
            try:
                target_url = reverse(url_name, kwargs=kwargs).rstrip('/')
                if current_path == target_url:
                    return css_class
            except:
                # If reverse fails (e.g., missing required kwargs), return empty
                return ''
        else:
            # If no kwargs, just return the css_class if URL name matches
            return css_class
    return ''
