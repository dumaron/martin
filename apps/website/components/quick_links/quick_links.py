from dataclasses import dataclass

from django.urls import reverse


@dataclass(frozen=True)
class QuickLink:
	label: str
	url: str


def quick_link(label: str, url_name: str, *args, **kwargs) -> QuickLink:
	"""
	Build one entry of a page's "Quick links" section.

	The URL is reversed here rather than in the template, so the shared partial only ever renders a label
	and an href, and a typo in a route name blows up while rendering the view instead of silently
	producing an empty link.

		quick_link('Add another root project', 'project_create_page.main_render')
		quick_link('Back to this project', 'project_detail_page.main_render', project.id)
		quick_link('Personal account', 'pair_transactions_page.main_render', kind='personal')
	"""
	return QuickLink(label=label, url=reverse(url_name, args=args, kwargs=kwargs))
