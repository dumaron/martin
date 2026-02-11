import django_tables2 as tables
from django.shortcuts import get_object_or_404, render

from apps.website.pages.page import Page
from core.models import Document, File


class FileTable(tables.Table):
	id = tables.Column(verbose_name='ID')
	file = tables.Column(verbose_name='File Path')
	uploaded_at = tables.DateTimeColumn(verbose_name='Uploaded At', format='Y-m-d H:i')

	class Meta:
		model = File
		template_name = 'django_tables2/table.html'
		fields = ('id', 'file', 'uploaded_at')


page = Page(name='document_detail_page', base_route='models/document/<int:document_id>')


@page.main
def main_render(request, document_id):
	document = get_object_or_404(Document, pk=document_id)
	files = File.objects.filter(document=document).order_by('-uploaded_at')

	files_table = FileTable(files)
	tables.RequestConfig(request, paginate=False).configure(files_table)
	return render(
		request,
		'document_detail/document_detail.html',
		{'document': document, 'files': files, 'files_table': files_table},
	)
