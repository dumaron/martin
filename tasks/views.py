from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from .models import Project, Todo
from django.db.models import Max



@login_required
@require_GET
def first_page(request):
    """
    TODO
    """
    top_level_projects = Project.objects.filter(tn_parent__isnull=True, status=Project.Statuses.ACTIVE)
    return render(request, 'first_page.html', { 'projects': top_level_projects })


@login_required
@require_GET
def project_detail(request, project_id):
    """
    TODO
    """
    project = get_object_or_404(Project, pk=project_id)
    children_projects = Project.objects.filter(tn_parent=project, status=Project.Statuses.ACTIVE)
    related_todos = Todo.objects.filter(project=project).order_by('description')
    return render(request, 'project.html', {
        'project': project,
        'todos': related_todos,
        'children_projects': children_projects,
    })


def flows_list(request):
    """
    TODO
    """
    return render(request, 'flows_list.html', {})


def process_tasks_by_priority_flow(request):
    """
    TODO
    """

    max_priority_todo = Todo.objects.filter(status=Todo.Statuses.TODO).order_by('-priority').first()

    return render(request, 'flows/process_tasks_by_priority.html', { 'todo': max_priority_todo })