from django.contrib import admin
from .models import Project, Todo, Inbox, Update
from treenode.admin import TreeNodeModelAdmin
from treenode.forms import TreeNodeForm

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

class ProjectAdmin(TreeNodeModelAdmin):
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_ACCORDION
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_BREADCRUMBS
    treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_INDENTATION

    # use TreeNodeForm to automatically exclude invalid parent choices
    form = TreeNodeForm

    list_display = ['name', 'status']

    search_fields = ['name']

    list_filter = ['status']


admin.site.register(Project, ProjectAdmin)
admin.site.register(Todo, TodoModelAdmin)
admin.site.register(Inbox, InboxModelAdmin)
admin.site.register(Update)
