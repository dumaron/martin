from django.shortcuts import render

from apps.website.pages.page import Page
from core.models import Project

page = Page(name='projects_page', base_route='pages/projects')


@page.main
def main_render(request):
	# Get only root projects that are active (projects without a parent)
	root_projects = Project.objects.filter(parent__isnull=True, status='active')
	return render(request, 'projects/projects.html', {'root_projects': root_projects})
