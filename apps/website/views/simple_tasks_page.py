from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.website.forms import TaskForm
from core.models import Project, Task


@login_required
def simple_tasks_page(request):
	if request.method == 'POST':
		form = TaskForm(request.POST)
		if form.is_valid():
			form.save()

	clean_form = TaskForm()
	tasks = Task.objects.filter(status__in=['pending', 'active'])
	return render(request, 'simple_tasks.html', {'tasks': tasks, 'form': clean_form})


@login_required
@require_POST
def task_create(request, project_id):
	project = get_object_or_404(Project, pk=project_id)

	if request.method == 'POST':
		form = TaskForm(request.POST)
		if form.is_valid():
			task = form.save(commit=False)
			task.project = project
			task.save()
			return redirect('project_detail', project_id=project.id)
	else:
		form = TaskForm()

	return render(request, 'task_create.html', {'project': project, 'form': form})


@login_required
@require_POST
def mark_task_as_completed(request):
	task_id = int(request.POST.get('task_id'))
	task = get_object_or_404(Task, pk=task_id)

	if task.status != 'completed':
		task.status = 'completed'
		task.completed_at = timezone.now()
		task.save()

	return redirect('simple_tasks_page')


@login_required
@require_POST
def abort_task(request):
	task_id = int(request.POST.get('task_id'))
	task = get_object_or_404(Task, pk=task_id)

	if task.status != 'aborted':
		task.status = 'aborted'
		task.completed_at = None
		task.save()

	return redirect('simple_tasks_page')
