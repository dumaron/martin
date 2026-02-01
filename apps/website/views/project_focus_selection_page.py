from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.models import Project
from utils.failures import Failure


@login_required
@require_GET
def main_render(request):
	active_projects = Project.objects.filter(status='active')
	inactive_projects = Project.objects.filter(status__in=['pending', 'suspended'])
	return render(
		request,
		'project_focus_selection.html',
		{
			'active_projects': active_projects,
			'inactive_projects': inactive_projects,
			'max_active': Project.max_global_active_number,
		},
	)


@login_required
@require_POST
def promote_projects(request):
	project_ids = request.POST.getlist('project_ids')
	for project_id in project_ids:
		project = get_object_or_404(Project, pk=project_id)
		result = project.promote_to_active()
		if isinstance(result, Failure):
			messages.error(request, result.reason)
			break
	return redirect('project_focus_selection_page.main_render')


@login_required
@require_POST
def suspend_projects(request):
	project_ids = request.POST.getlist('project_ids')
	if project_ids:
		Project.objects.filter(id__in=project_ids).update(status='suspended')
	return redirect('project_focus_selection_page.main_render')
