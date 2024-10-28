from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('finances/', include('finances.urls')),
    path('tasks/', include('tasks.urls')),
    path('memory/', include('memory.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
