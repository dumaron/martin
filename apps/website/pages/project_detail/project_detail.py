from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.website.pages.page import Page
from core.models import Project, Task


class ProjectStatusForm(forms.Form):
	status = forms.ChoiceField(
		choices=[('', 'Choose status...')] + Project.STATUS_CHOICES,
		widget=forms.Select(attrs={'class': 'tom-select'}),
	)


page = Page(name='project_detail_page', base_route='models/project/<int:project_id>')


@page.main
def main_render(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	tasks = project.tasks.all()
	status_form = ProjectStatusForm(initial={'status': project.status})
	return render(
		request,
		'project_detail/project_detail.html',
		{'project': project, 'tasks': tasks, 'status_form': status_form},
	)


@page.action('update-status')
def update_status(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	form = ProjectStatusForm(request.POST)

	if form.is_valid():
		new_status = form.cleaned_data['status']
		if new_status:  # Make sure it's not empty
			project.status = new_status
			project.save()

	return redirect('project_detail_page.main_render', project_id=project.id)


@page.action('mark_task_complete')
def mark_task_complete(request, project_id):
	task_id = int(request.POST.get('task_id'))
	task = get_object_or_404(Task, pk=task_id)

	task.mark_as_completed()

	return redirect('project_detail_page.main_render', project_id=project_id)


@page.partial('add-task-form')
def add_task_form(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	return render(request, 'project_detail/add_task_form.html', {'project': project})


@page.action('create-task')
def create_task(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	description = request.POST.get('description', '').strip()

	if description:
		task = Task.objects.create(project=project, description=description, status='pending')
		return render(request, 'project_detail/task_item.html', {'task': task})

	return render(request, 'project_detail/add_task_form.html', {'project': project})


@page.partial('add-subproject-form')
def add_subproject_form(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	return render(request, 'project_detail/add_subproject_form.html', {'project': project})


@page.action('create-subproject')
def create_subproject(request, project_id):
	parent_project = get_object_or_404(Project, pk=project_id)
	title = request.POST.get('title', '').strip()

	if title:
		subproject = Project.objects.create(title=title, parent=parent_project, status='active')
		return render(request, 'project_detail/subproject_item.html', {'subproject': subproject})

	return render(request, 'project_detail/add_subproject_form.html', {'project': parent_project})


@page.action(route='models/project/mark-tasks-complete')
def mark_tasks_complete(request):
	task_ids = request.POST.getlist('task_ids')

	if task_ids:
		Task.objects.filter(id__in=task_ids).update(status='completed', completed_at=timezone.now())

	return redirect('projects_page.main_render')
