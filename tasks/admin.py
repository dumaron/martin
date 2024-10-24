from django.contrib import admin
from .models import Project, Todo, Inbox, Update


class TodoModelAdmin(admin.ModelAdmin):
    list_display = ['description', 'project', 'priority', 'status', 'deadline']
    search_fields = ['description']
    list_filter = [
        'status',
        'is_valid_order_pray',
    ]


class InboxModelAdmin(admin.ModelAdmin):
    list_display = ['content', 'context', 'created_at', 'processed_at', 'deleted_at']
    search_field = ['content']
    list_filter = [
        'context',
        ('processed_at', admin.EmptyFieldListFilter),
        ('deleted_at', admin.EmptyFieldListFilter),
    ]

admin.site.register(Project)
admin.site.register(Todo, TodoModelAdmin)
admin.site.register(Inbox, InboxModelAdmin)
admin.site.register(Update)
