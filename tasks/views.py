from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from .models import Project, Todo


@login_required
def first_page(request):
    top_level_projects = Project.objects.filter(tn_parent__isnull=True, status=Project.Statuses.ACTIVE)
    return render(request, 'first_page.html', { 'projects': top_level_projects })


@login_required
@require_GET
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    children_projects = Project.objects.filter(tn_parent=project, status=Project.Statuses.ACTIVE)
    related_todos = Todo.objects.filter(project=project).order_by('description')
    return render(request, 'project.html', {
        'project': project,
        'todos': related_todos,
        'children_projects': children_projects,
    })
