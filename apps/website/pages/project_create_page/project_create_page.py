from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.models import Project


class ProjectForm(forms.ModelForm):
	class Meta:
		model = Project
		fields = ['title', 'goal']
		widgets = {
			'title': forms.TextInput(attrs={'placeholder': 'Enter project title'}),
			'goal': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional project goal'}),
		}


@login_required
@require_GET
def main_render(request):
	form = ProjectForm()
	return render(request, 'project_create_page/project_create.html', {'form': form})


@login_required
@require_POST
def create_project(request):
	form = ProjectForm(request.POST)
	if form.is_valid():
		project = form.save()
		return redirect('project_detail_page.main_render', project_id=project.id)
	return render(request, 'project_create_page/project_create.html', {'form': form})
