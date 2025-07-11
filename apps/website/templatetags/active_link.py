from django import template
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

register = template.Library()

@register.simple_tag
def active(request, url_name, css_class='active', match_children=True, **kwargs):
    """
    Returns the css_class if the current request URL matches the named URL.
    If kwargs are provided, it also checks that the URL parameters match.
    If match_children is True, also matches when current_path starts with target_url.
    """
    # Normalize paths by removing trailing slashes
    current_path = request.path.rstrip('/')
    
    try:
        # Get the target URL
        target_url = reverse(url_name, kwargs=kwargs).rstrip('/')
        
        # Check for exact match first
        if current_path == target_url:
            return css_class
        
        # Check for child page match if enabled
        if match_children and target_url and current_path.startswith(target_url + '/'):
            return css_class
            
    except:
        # If reverse fails, try fallback URL name matching for compatibility
        try:
            resolved = resolve(request.path)
            if resolved.url_name == url_name and not kwargs:
                return css_class
        except:
            # If resolve also fails, we can't do any matching
            pass
        
    return ''
