from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from core.models import Project, Task


class TaskForm(forms.ModelForm):
	class Meta:
		model = Task
		fields = ['description', 'project']
		widgets = {
			'description': forms.TextInput(attrs={'placeholder': 'Enter task description'}),
			'project': forms.Select(attrs={'class': 'tom-select'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['project'].empty_label = 'No project (standalone task)'
		self.fields['project'].required = False


@login_required
@require_GET
def simple_tasks_page(request):
	clean_form = TaskForm()
	tasks = Task.objects.filter(status__in=['pending', 'active'])
	return render(request, 'simple_tasks.html', {'tasks': tasks, 'form': clean_form})


@login_required
@require_POST
def task_create(request):
	form = TaskForm(request.POST)

	if form.is_valid():
		task = form.save(commit=False)
		task.save()

	return redirect('simple_tasks_page.main_render')


@login_required
@require_POST
def mark_task_as_completed(request):
	task_id = int(request.POST.get('task_id'))
	task = get_object_or_404(Task, pk=task_id)
	# TODO make this mutation a single method on the model
	if task.status != 'completed':
		task.status = 'completed'
		task.completed_at = timezone.now()
		task.save()

	return redirect('simple_tasks_page.main_render')


@login_required
@require_POST
def abort_task(request):
	task_id = int(request.POST.get('task_id'))
	task = get_object_or_404(Task, pk=task_id)

	if task.status != 'aborted':
		task.status = 'aborted'
		task.completed_at = None
		task.save()

	return redirect('simple_tasks_page.main_render')
