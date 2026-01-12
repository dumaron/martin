from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from core.models import Project, Task


class ProjectStatusForm(forms.Form):
	status = forms.ChoiceField(
		choices=[('', 'Choose status...')] + Project.STATUS_CHOICES,
		widget=forms.Select(attrs={'class': 'tom-select'}),
	)


@login_required
@require_GET
def main_render(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	tasks = project.tasks.all()
	status_form = ProjectStatusForm(initial={'status': project.status})
	return render(
		request, 'project_detail.html', {'project': project, 'tasks': tasks, 'status_form': status_form}
	)


@login_required
@require_POST
def update_status(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	form = ProjectStatusForm(request.POST)

	if form.is_valid():
		new_status = form.cleaned_data['status']
		if new_status:  # Make sure it's not empty
			project.status = new_status
			project.save()

	return redirect('project_detail_page.main_render', project_id=project.id)


@login_required
@require_POST
def mark_task_complete(request, project_id):
	task_id = int(request.POST.get('task_id'))
	task = get_object_or_404(Task, pk=task_id)

	# TODO make this mutation a single method on the model
	if task.status != 'completed':
		task.status = 'completed'
		task.completed_at = timezone.now()
		task.save()

	return redirect('project_detail_page.main_render', project_id=project_id)


@login_required
@require_GET
def add_task_form(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	return render(request, 'partials/add_task_form.html', {'project': project})


@login_required
@require_POST
def create_task(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	description = request.POST.get('description', '').strip()

	if description:
		task = Task.objects.create(project=project, description=description, status='pending')
		return render(request, 'partials/task_item.html', {'task': task})

	return render(request, 'partials/add_task_form.html', {'project': project})


@login_required
@require_GET
def add_subproject_form(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	return render(request, 'partials/add_subproject_form.html', {'project': project})


@login_required
@require_POST
def create_subproject(request, project_id):
	parent_project = get_object_or_404(Project, pk=project_id)
	title = request.POST.get('title', '').strip()

	if title:
		subproject = Project.objects.create(title=title, parent=parent_project, status='active')
		return render(request, 'partials/subproject_item.html', {'subproject': subproject})

	return render(request, 'partials/add_subproject_form.html', {'project': parent_project})


@login_required
@require_POST
def mark_tasks_complete(request):
	task_ids = request.POST.getlist('task_ids')

	if task_ids:
		Task.objects.filter(id__in=task_ids).update(status='completed', completed_at=timezone.now())

	return redirect('project_list_page.main_render')
