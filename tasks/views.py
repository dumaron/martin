from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from .models import Project, Todo, Inbox
from django.http import HttpResponseBadRequest
from datetime import datetime


@login_required
@require_GET
def first_page(request):
    """
    TODO
    """
    top_level_projects = Project.objects.filter(tn_parent__isnull=True, status=Project.Statuses.ACTIVE)
    return render(request, 'first_page.html', { 'projects': top_level_projects })


@login_required
@require_GET
def project_detail(request, project_id):
    """
    TODO
    """
    project = get_object_or_404(Project, pk=project_id)
    children_projects = Project.objects.filter(tn_parent=project, status=Project.Statuses.ACTIVE)
    related_todos = Todo.objects.filter(project=project).order_by('description')
    return render(request, 'project.html', {
        'project': project,
        'todos': related_todos,
        'children_projects': children_projects,
    })


@login_required
@require_GET
def flows_list(request):
    """
    Renders the initial page for the flows section
    """
    return render(request, 'flows_list.html', {})


@login_required
@require_GET
def process_tasks_by_priority_flow(request):
    """
    Flow that presents the task with the highest priority among the ones that needs to be done
    """

    max_priority_todo = Todo.objects.filter(status=Todo.Statuses.TODO).order_by('-priority').first()
    return render(request, 'flows/process_tasks_by_priority.html', { 'todo': max_priority_todo })


@login_required
@require_POST
def set_task_status(request, todo_id):
    """

    """

    todo = get_object_or_404(Todo, pk=todo_id)
    todo.status = request.POST['new-status']
    todo.save()

    return


@login_required
@require_GET
def process_inboxes_flow(request):
    """
    Flow to take inboxes one by one ordered by creation date, and to process them. Should foster their usage, as right
    now they are almost unused.
    """

    oldest_unprocessed_inbox = Inbox.objects.filter(processed_at__isnull=True, deleted_at__isnull=True).order_by('created_at').first()
    return render(request, 'flows/process_inboxes.html', { 'inbox': oldest_unprocessed_inbox })


@login_required
@require_POST
def process_inbox(request, inbox_id):
    """
    Updates an inbox by setting it as deleted or processed depending on the submitted value
    """

    inbox = get_object_or_404(Inbox, pk=inbox_id)
    mark_as_processed = request.POST['status'] == 'processed'
    mark_as_deleted = request.POST['status'] == 'deleted'

    if not mark_as_processed and not mark_as_deleted:
        return HttpResponseBadRequest('Invalid status update for Inbox object')

    if mark_as_processed:
        inbox.processed_at = datetime.now()

    if mark_as_deleted:
        inbox.deleted_at = datetime.now()

    inbox.save()

    return redirect('process_inboxes_flow')