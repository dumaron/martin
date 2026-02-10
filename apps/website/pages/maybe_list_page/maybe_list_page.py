from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.models import Maybe


@login_required
@require_GET
def main_render(request):
	open_maybes = Maybe.objects.filter(status='open')
	return render(request, 'maybe_list_page/maybe_list.html', {'open_maybes': open_maybes})


@login_required
@require_POST
def promote_to_project(request):
	maybe_id = request.POST.get('maybe_id')
	maybe = get_object_or_404(Maybe, pk=maybe_id)
	project = maybe.promote_to_project()
	return redirect('project_detail_page.main_render', project_id=project.id)


@login_required
@require_POST
def dismiss(request):
	maybe_id = request.POST.get('maybe_id')
	maybe = get_object_or_404(Maybe, pk=maybe_id)
	maybe.dismiss()
	return redirect('maybe_list_page.main_render')


@login_required
@require_GET
def add_form(request):
	return render(request, 'maybe_list_page/maybe_add_form.html')


@login_required
@require_POST
def create(request):
	title = request.POST.get('title', '').strip()
	notes = request.POST.get('notes', '').strip()

	if title:
		maybe = Maybe.objects.create(title=title, notes=notes)
		return render(request, 'maybe_list_page/maybe_row.html', {'maybe': maybe})

	return render(request, 'maybe_list_page/maybe_add_form.html')
