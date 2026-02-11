from django import forms
from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
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
