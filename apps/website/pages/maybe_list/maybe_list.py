from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core.models import Maybe

page = Page(name='maybe_list_page', base_route='models/maybe')


@page.main
def main_render(request):
	open_maybes = Maybe.objects.filter(status='open')
	return render(request, 'maybe_list/maybe_list.html', {'open_maybes': open_maybes})


@page.action('promote')
def promote_to_project(request):
	maybe_id = request.POST.get('maybe_id')
	maybe = get_object_or_404(Maybe, pk=maybe_id)
	project = maybe.promote_to_project()
	return redirect('project_detail_page.main_render', project_id=project.id)


@page.action('dismiss')
def dismiss(request):
	maybe_id = request.POST.get('maybe_id')
	maybe = get_object_or_404(Maybe, pk=maybe_id)
	maybe.dismiss()
	return redirect('maybe_list_page.main_render')


@page.partial('add-form')
def add_form(request):
	return render(request, 'maybe_list/maybe_add_form.html')


@page.action('create')
def create(request):
	title = request.POST.get('title', '').strip()
	notes = request.POST.get('notes', '').strip()

	if title:
		maybe = Maybe.objects.create(title=title, notes=notes)
		return render(request, 'maybe_list/maybe_row.html', {'maybe': maybe})

	return render(request, 'maybe_list/maybe_add_form.html')
