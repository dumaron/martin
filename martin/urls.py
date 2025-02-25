from django.contrib import admin
from django.urls import path, include

from .views import martin_home_page

urlpatterns = [
    path('', martin_home_page, name='martin_home_page'),
    path('admin/', admin.site.urls),
    path('finances/', include('finances.urls')),
    path('tasks/', include('tasks.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
