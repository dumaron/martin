from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.website.pages.page import Page
from core.models import Project, Task

page = Page(name='projects_page', base_route='pages/projects')


@page.main
def main_render(request):
	root_projects = Project.objects.filter(parent__isnull=True, status='active')
	orphan_tasks = Task.objects.filter(project__isnull=True, status='pending')

	return render(
		request, 'projects/projects.html', {'root_projects': root_projects, 'orphan_tasks': orphan_tasks}
	)


@page.partial('add-orphan-task-form')
def add_orphan_task_form(request):
	return render(request, 'projects/add_orphan_task_form.html')


@page.action('create-orphan-task')
def create_orphan_task(request):
	description = request.POST.get('description', '').strip()

	if description:
		task = Task.objects.create(description=description, status='pending')
		return render(request, 'projects/task_item.html', {'task': task})

	return render(request, 'projects/add_orphan_task_form.html')


@page.partial('<int:project_id>/add-task-form')
def add_project_task_form(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	return render(request, 'projects/add_task_form.html', {'project': project})


@page.action('<int:project_id>/create-task')
def create_project_task(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	description = request.POST.get('description', '').strip()

	if description:
		task = Task.objects.create(project=project, description=description, status='pending')
		return render(request, 'projects/task_item.html', {'task': task})

	return render(request, 'projects/add_task_form.html', {'project': project})


@page.partial('<int:project_id>/add-subproject-form')
def add_subproject_form(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	return render(request, 'projects/add_subproject_form.html', {'project': project})


@page.action('<int:project_id>/create-subproject')
def create_subproject(request, project_id):
	parent_project = get_object_or_404(Project, pk=project_id)
	title = request.POST.get('title', '').strip()

	if title:
		subproject = Project.objects.create(title=title, parent=parent_project, status='active')
		return render(request, 'projects/subproject_item.html', {'subproject': subproject})

	return render(request, 'projects/add_subproject_form.html', {'project': parent_project})


@page.partial('task/<int:task_id>/detail')
def task_detail(request, task_id):
	task = get_object_or_404(Task, pk=task_id)
	return render(request, 'projects/task_detail.html', {'task': task})


@page.action('task/<int:task_id>/update-status')
def update_task_status(request, task_id):
	task = get_object_or_404(Task, pk=task_id)
	new_status = request.POST.get('status', '').strip()

	status_handlers = {'completed': lambda t: t.mark_as_completed(), 'aborted': lambda t: t.abort()}

	handler = status_handlers.get(new_status)
	if handler:
		handler(task)
	elif new_status in ('pending', 'active'):
		task.status = new_status
		task.save()

	return redirect('projects_page.main_render')


@page.action('mark-tasks-complete')
def mark_tasks_complete(request):
	task_ids = request.POST.getlist('task_ids')

	if task_ids:
		Task.objects.filter(id__in=task_ids).update(status='completed', completed_at=timezone.now())

	return redirect('projects_page.main_render')
