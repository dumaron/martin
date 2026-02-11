from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.website import pages

"""
After some back and forth on what URLs should represent, I decided to go with an approach where they represent HTML
pages and actions (intended as form submit). So they are more representation-oriented than model-oriented. They take
inspiration more from the old PHP world than the REST approach which appeared a couple years after the first.

Everything is coupled in a reasonable way IMHO:
	>>> code is shaped after how the user (me) will use the application. <<<

Enjoy the benefit of not having to make everything generic: too much decoupling can be harmful in context where it's not
needed. If more "frontends" (intended as API, telegram bots, etc.) will be added, then we might have an actual reason to
rework coupling.

I know that the URLs nesting structure is somewhat incorrect. After all, why putting things under `/pages`
if no `/pages` page exists? But I think it helps me reason for now. If you notice, URls also don't match with the
breadcrumbs, which don't match with the navigation menu. Things are moving a lot, I'm learning and reasoning, keep peace
with things being messy and not perfect.

"""

urlpatterns = [
	path(route='admin/', view=admin.site.urls),
	path(route='accounts/', view=include('django.contrib.auth.urls')),
	#
	*pages.welcome.page.get_urls(),
	*pages.pair_transactions.page.get_urls(),
	*pages.process_inboxes.page.get_urls(),
	*pages.capture_inbox.page.get_urls(),
	*pages.daily_suggestions_intro.page.get_urls(),
	*pages.daily_suggestion_detail.page.get_urls(),
	*pages.bank_export_import.page.get_urls(),
	*pages.ynab_integration.page.get_urls(),
	*pages.bank_file_import_list.page.get_urls(),
	*pages.bank_file_import_detail.page.get_urls(),
	*pages.bank_transaction_list.page.get_urls(),
	*pages.bank_transaction_detail.page.get_urls(),
	*pages.ynab_transaction_detail.page.get_urls(),
	*pages.event_list.page.get_urls(),
	*pages.event_create.page.get_urls(),
	*pages.event_detail.page.get_urls(),
	*pages.document_list.page.get_urls(),
	*pages.document_create.page.get_urls(),
	*pages.document_detail.page.get_urls(),
	*pages.projects.page.get_urls(),
	*pages.maybe_list.page.get_urls(),
	*pages.project_create.page.get_urls(),
	*pages.project_detail.page.get_urls(),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
