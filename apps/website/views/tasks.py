from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.website.forms import TaskForm
from core.models import Project, Task


@login_required
def task_create(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	
	if request.method == 'POST':
		form = TaskForm(request.POST)
		if form.is_valid():
			task = form.save(commit=False)
			task.project = project
			task.save()
			messages.success(request, f'Task "{task.title}" added to project!')
			return redirect('project_detail', project_id=project.id)
	else:
		form = TaskForm()
	
	return render(request, 'task_create.html', {'project': project, 'form': form})


@login_required
@require_POST
def task_mark_done(request, task_id):
	task = get_object_or_404(Task, pk=task_id)
	
	if not task.is_done:
		task.is_done = True
		task.completed_at = timezone.now()
		task.save()
		messages.success(request, f'Task "{task.title}" marked as done!')
	else:
		task.is_done = False
		task.completed_at = None
		task.save()
		messages.success(request, f'Task "{task.title}" reopened!')
	
	return redirect('project_detail', project_id=task.project.id)