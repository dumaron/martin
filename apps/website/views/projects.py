import django_tables2 as tables
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.website.forms import ProjectForm, ProjectStatusForm
from core.models import Project


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
		status_icons = {
			'active': '▶️',
			'suspended': '⏸️',
			'archived': '📦',
			'done': '✅',
		}
		return f'{status_icons.get(record.status, "")} {record.get_status_display()}'


@login_required
@require_GET
def project_list(request):
	projects = Project.objects.all()
	table = ProjectTable(projects)
	return render(request, 'project_list.html', {'table': table})


@login_required
@require_GET
def project_detail(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	tasks = project.tasks.all()
	status_form = ProjectStatusForm(initial={'status': project.status})
	return render(request, 'project_detail.html', {
		'project': project, 
		'tasks': tasks, 
		'status_form': status_form
	})


@login_required
def project_create(request):
	if request.method == 'POST':
		form = ProjectForm(request.POST)
		if form.is_valid():
			project = form.save()
			messages.success(request, f'Project "{project.title}" created successfully!')
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
			messages.success(request, f'Project status updated to {project.get_status_display()}')
		else:
			messages.error(request, 'Please select a status')
	else:
		messages.error(request, 'Invalid status')
	
	return redirect('project_detail', project_id=project.id)