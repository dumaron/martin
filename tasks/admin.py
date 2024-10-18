from django.contrib import admin
from .models import Project, Todo, Inbox, Update

admin.site.register(Project)
admin.site.register(Todo)
admin.site.register(Inbox)
admin.site.register(Update)
