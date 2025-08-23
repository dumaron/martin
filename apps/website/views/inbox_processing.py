import django_tables2 as tables
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.website.forms import InboxForm
from core.models import Inbox, Project, Task


class InboxTable(tables.Table):
	content = tables.LinkColumn('inbox_detail', args=[tables.A('pk')], verbose_name='Content')
	created_at = tables.DateTimeColumn(verbose_name='Created', format='Y-m-d H:i')
	processed = tables.BooleanColumn(verbose_name='Processed', yesno='✓,◯')

	class Meta:
		model = Inbox
		template_name = 'django_tables2/table.html'
		fields = ('content', 'created_at', 'processed')


@login_required
@require_GET
def inbox_list(request):
	inboxes = Inbox.objects.all()
	table = InboxTable(inboxes)
	return render(request, 'inbox_list.html', {'table': table})


@login_required
def inbox_create(request):
	if request.method == 'POST':
		form = InboxForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Inbox item created successfully!')
			return redirect('inbox_list')
	else:
		form = InboxForm()
	
	return render(request, 'inbox_create.html', {'form': form})


@login_required
@require_GET
def inbox_detail(request, inbox_id):
	inbox = get_object_or_404(Inbox, pk=inbox_id)
	return render(request, 'inbox_detail.html', {'inbox': inbox})


@login_required
@require_GET
def flow_page(request):
	# Get the oldest unprocessed inbox item
	oldest_inbox = Inbox.objects.filter(processed=False).order_by('created_at').first()
	
	if not oldest_inbox:
		messages.info(request, 'No unprocessed inbox items!')
		return redirect('inbox_list')
	
	projects = Project.objects.filter(status='active')
	return render(request, 'flow_page.html', {'inbox': oldest_inbox, 'projects': projects})


@login_required
@require_POST
def process_inbox_item(request, inbox_id):
	inbox = get_object_or_404(Inbox, pk=inbox_id)
	action = request.POST.get('action')
	
	if action == 'create_project':
		title = request.POST.get('project_title')
		description = request.POST.get('project_description', '')
		
		if title:
			project = Project.objects.create(title=title, description=description)
			inbox.created_project = project
			inbox.processed = True
			inbox.processed_at = timezone.now()
			inbox.save()
			messages.success(request, f'Created project "{project.title}" from inbox item!')
		else:
			messages.error(request, 'Project title is required.')
			return redirect('flow_page')
	
	elif action == 'create_task':
		project_id = request.POST.get('project_id')
		title = request.POST.get('task_title')
		description = request.POST.get('task_description', '')
		
		if project_id and title:
			project = get_object_or_404(Project, pk=project_id)
			task = Task.objects.create(title=title, description=description, project=project)
			inbox.created_task = task
			inbox.processed = True
			inbox.processed_at = timezone.now()
			inbox.save()
			messages.success(request, f'Created task "{task.title}" in project "{project.title}" from inbox item!')
		else:
			messages.error(request, 'Project and task title are required.')
			return redirect('flow_page')
	
	elif action == 'mark_done':
		inbox.processed = True
		inbox.processed_at = timezone.now()
		inbox.save()
		messages.success(request, 'Inbox item marked as processed.')
	
	return redirect('flow_page')