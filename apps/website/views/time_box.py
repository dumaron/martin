
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import TimeBox


@require_GET
def time_box_page(request):
    """
    Renders the time box page.
    """

    current_active_time_box = TimeBox.get_active_time_box()
    return render(request, 'time_box_flow_page.html', {'actve_time_box': current_active_time_box})



