import django_tables2 as tables
from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from core.models import Project, Task


class ProjectForm(forms.ModelForm):
	class Meta:
		model = Project
		fields = ['title', 'description']
		widgets = {
			'title': forms.TextInput(attrs={'placeholder': 'Enter project title'}),
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional project description'}),
		}


class ProjectStatusForm(forms.Form):
	status = forms.ChoiceField(
		choices=[('', 'Choose status...')] + Project.STATUS_CHOICES,
		widget=forms.Select(attrs={'class': 'tom-select'}),
	)


class ProjectTable(tables.Table):
	title = tables.LinkColumn('project_detail', args=[tables.A('pk')], verbose_name='Title')
	status = tables.Column(verbose_name='Status')
	task_count = tables.Column(empty_values=(), verbose_name='Tasks')
	created_at = tables.DateTimeColumn(verbose_name='Created', format='Y-m-d H:i')

	class Meta:
		model = Project
		template_name = 'django_tables2/table.html'
		fields = ('title', 'status', 'task_count', 'created_at')

	def render_task_count(self, record):
		done_count = record.tasks.filter(status=['pending', 'active']).count()
		total_count = record.tasks.count()
		return f'{done_count}/{total_count}'

	def render_status(self, record):
		status_icons = {'active': '▶️', 'suspended': '⏸️', 'archived': '📦', 'done': '✅'}
		return f'{status_icons.get(record.status, "")} {record.get_status_display()}'


@login_required
@require_GET
def project_list(request):
	# Get only root projects that are active (projects without a parent)
	root_projects = Project.objects.filter(parent__isnull=True, status='active')
	return render(request, 'project_list.html', {'root_projects': root_projects})


@login_required
@require_GET
def project_detail(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	tasks = project.tasks.all()
	status_form = ProjectStatusForm(initial={'status': project.status})
	return render(
		request, 'project_detail.html', {'project': project, 'tasks': tasks, 'status_form': status_form}
	)


@login_required
def project_create(request):
	if request.method == 'POST':
		form = ProjectForm(request.POST)
		if form.is_valid():
			project = form.save()
			return redirect('project_detail', project_id=project.id)
	else:
		form = ProjectForm()

	return render(request, 'project_create.html', {'form': form})


@login_required
@require_POST
def project_update_status(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	form = ProjectStatusForm(request.POST)

	if form.is_valid():
		new_status = form.cleaned_data['status']
		if new_status:  # Make sure it's not empty
			project.status = new_status
			project.save()

	return redirect('project_detail', project_id=project.id)


@login_required
@require_POST
def mark_task_as_completed(request, project_id):
	task_id = int(request.POST.get('task_id'))
	task = get_object_or_404(Task, pk=task_id)

	# TODO make this mutation a single method on the model
	if task.status != 'completed':
		task.status = 'completed'
		task.completed_at = timezone.now()
		task.save()

	return redirect('project_detail', project_id=project_id)


@login_required
@require_GET
def get_add_task_form(request, project_id):
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
def get_add_subproject_form(request, project_id):
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

	return redirect('project_list')
