from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET


@login_required
@require_GET
def martin_home_page(request):
	"""
	The Martin initial page. Tomorrow it'll contain pictures of the people I love, or inspiring quotes/images.
	Right now, I need to adapt.
	"""

	return render(request, 'home.html', {})