from django.shortcuts import render

def first_page(request):
    return render(request, 'homepage.html', {})
