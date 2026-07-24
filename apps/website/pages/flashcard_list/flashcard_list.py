import django_tables2 as tables
from django.shortcuts import render
from django.utils.html import format_html_join
from django.utils.text import Truncator

from apps.website.pages.page import Page
from core.models import Flashcard


class FlashcardTable(tables.Table):
	id = tables.LinkColumn('flashcard_edit_page.main_render', args=[tables.A('pk')], verbose_name='ID')
	question = tables.Column(verbose_name='Question')
	state = tables.Column(verbose_name='State')
	due = tables.DateTimeColumn(verbose_name='Due', format='Y-m-d H:i')
	tags = tables.Column(verbose_name='Tags', empty_values=(), orderable=False)

	class Meta:
		model = Flashcard
		template_name = 'django_tables2/table.html'
		fields = ('id', 'question', 'state', 'due', 'tags')

	def render_question(self, value):
		return Truncator(value).chars(80)

	def render_state(self, record):
		return record.get_state_display()

	def render_tags(self, record):
		return format_html_join(
			', ', '<a href="?tag={}">{}</a>', map(lambda tag: (tag.name, tag.name), record.tags.all())
		)


page = Page(name='flashcard_list_page', base_route='models/flashcard')


@page.main
def main_render(request):
	tag = request.GET.get('tag') or None

	queryset = Flashcard.objects.prefetch_related('tags').order_by('due')
	if tag:
		queryset = queryset.filter(tags__name=tag)

	table = FlashcardTable(queryset)
	tables.RequestConfig(request).configure(table)
	return render(request, 'flashcard_list/flashcard_list.html', {'table': table, 'tag': tag})
