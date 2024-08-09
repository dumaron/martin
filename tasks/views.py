from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def first_page(request):
    return render(request, 'first_page.html', {})
