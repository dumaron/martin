from django import forms
from django.shortcuts import redirect, render

from apps.website.pages.page import Page
from core.models import Project


class ProjectForm(forms.ModelForm):
	class Meta:
		model = Project
		fields = ['title', 'goal']
		widgets = {
			'title': forms.TextInput(attrs={'placeholder': 'Enter project title'}),
			'goal': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional project goal'}),
		}


page = Page(name='project_create_page', base_route='models/project')


@page.main('create')
def main_render(request):
	form = ProjectForm()
	return render(request, 'project_create/project_create.html', {'form': form})


@page.action('create-action')
def create_project(request):
	form = ProjectForm(request.POST)
	if form.is_valid():
		project = form.save()
		return redirect('project_detail_page.main_render', project_id=project.id)
	return render(request, 'project_create/project_create.html', {'form': form})
