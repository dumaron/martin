from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import Project


@login_required
@require_GET
def main_render(request):
	# Get only root projects that are active (projects without a parent)
	root_projects = Project.objects.filter(parent__isnull=True, status='active')
	return render(request, 'active_project_worktree.html', {'root_projects': root_projects})
