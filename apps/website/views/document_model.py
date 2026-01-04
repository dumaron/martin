import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.models import Document, File


class FileTable(tables.Table):
	id = tables.Column(verbose_name='ID')
	file = tables.Column(verbose_name='File Path')
	uploaded_at = tables.DateTimeColumn(verbose_name='Uploaded At')

	class Meta:
		model = File
		template_name = 'django_tables2/table.html'
		fields = ('id', 'file', 'uploaded_at')


class DocumentTable(tables.Table):
	id = tables.LinkColumn('document_detail', args=[tables.A('pk')], verbose_name='ID')
	name = tables.Column(verbose_name='Name')
	description = tables.Column(verbose_name='Description')
	location = tables.Column(verbose_name='Location')
	created_at = tables.DateTimeColumn(verbose_name='Created At')
	file_count = tables.Column(empty_values=(), verbose_name='Files')

	class Meta:
		model = Document
		template_name = 'django_tables2/table.html'
		fields = ('id', 'name', 'description', 'location', 'created_at', 'file_count')


@login_required
@require_GET
def document_detail(request, document_id):
	document = get_object_or_404(Document, pk=document_id)
	files = File.objects.filter(document=document).order_by('-uploaded_at')

	files_table = FileTable(files)
	tables.RequestConfig(request, paginate=False).configure(files_table)
	return render(
		request,
		'document_detail.html',
		{
			'document': document,
			'files': files,
			'files_table': files_table,
		},
	)


@login_required
@require_GET
def document_list(request):
	table = DocumentTable(
		Document.objects.annotate(file_count=Count('file')).order_by('-created_at')
	)
	tables.RequestConfig(request).configure(table)
	return render(request, 'document_list.html', {'table': table})
