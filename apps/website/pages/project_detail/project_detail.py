from django import forms
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from apps.website.components.quick_links import quick_link
from core.models import Project


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
		{
			'project': project,
			'tasks': tasks,
			'status_form': status_form,
			'updates': project.updates.all(),
			'quick_links': [
				quick_link('Add another root project', 'project_create_page.main_render'),
				quick_link('Go to project work tree', 'project_work_tree_page.main_render'),
			],
		},
	)


@page.action('save-notes')
def save_project_notes(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	project.save_notes(request.POST.get('notes', ''))

	return render(request, 'project_detail/partial_project_notes.html', {'project': project})


@page.action('create-update')
def create_project_update(request, project_id):
	project = get_object_or_404(Project, pk=project_id)
	content = request.POST.get('content', '').strip()

	if not content:
		return HttpResponseBadRequest('A project update needs some content')

	project.add_update(content)

	return render(
		request,
		'project_detail/partial_project_updates.html',
		{'project': project, 'updates': project.updates.all()},
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
