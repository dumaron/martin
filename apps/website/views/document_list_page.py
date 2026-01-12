import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.models import Document


class DocumentTable(tables.Table):
	id = tables.LinkColumn('document_detail_page.main_render', args=[tables.A('pk')], verbose_name='ID')
	name = tables.Column(verbose_name='Name')
	description = tables.Column(verbose_name='Description')
	location = tables.Column(verbose_name='Location')
	tags = tables.Column(empty_values=(), verbose_name='Tags', orderable=False)
	created_at = tables.DateTimeColumn(verbose_name='Created At', format='Y-m-d H:i')
	file_count = tables.Column(empty_values=(), verbose_name='Files')

	def render_tags(self, record):
		return ', '.join([tag.name for tag in record.tags.all()])

	class Meta:
		model = Document
		template_name = 'django_tables2/table.html'
		fields = ('id', 'name', 'description', 'location', 'tags', 'created_at', 'file_count')


@login_required
@require_GET
def main_render(request):
	table = DocumentTable(Document.objects.annotate(file_count=Count('file')).order_by('-created_at'))
	tables.RequestConfig(request).configure(table)
	return render(request, 'document_list.html', {'table': table})
