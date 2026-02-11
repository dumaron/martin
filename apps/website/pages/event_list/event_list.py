import django_tables2 as tables
from django.shortcuts import render

from apps.website.pages.page import Page
from core.models import Event


class EventTable(tables.Table):
	id = tables.LinkColumn('event_detail_page.main_render', args=[tables.A('pk')], verbose_name='ID')
	description = tables.Column(verbose_name='Description')
	date = tables.DateColumn(verbose_name='Date', format='Y-m-d')
	time = tables.TimeColumn(verbose_name='Time', format='H:i')
	created_at = tables.DateTimeColumn(verbose_name='Created At', format='Y-m-d H:i')

	class Meta:
		model = Event
		template_name = 'django_tables2/table.html'
		fields = ('id', 'description', 'date', 'time', 'created_at')


page = Page(name='event_list_page', base_route='models/event')


@page.main
def main_render(request):
	table = EventTable(Event.objects.order_by('-date', '-time'))
	tables.RequestConfig(request).configure(table)
	return render(request, 'event_list/event_list.html', {'table': table})
