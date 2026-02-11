from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.http import require_GET, require_POST


class Page:
	"""
	Groups related views for a single page: main render, actions, and HTMX partials.

	Automatically applies @login_required and @require_GET/@require_POST based on
	the registration type. When migrating existing views, remove those decorators
	from the functions themselves.

	Usage:

		page = Page(name='maybe_list_page', base_route='models/maybe')

		@page.main
		def main_render(request):
			return render(request, 'maybe_list/maybe_list.html', {...})

		@page.action('create')
		def create(request):
			...

		@page.partial('add-form')
		def add_form(request):
			return render(request, 'maybe_list/maybe_add_form.html')

	In urls.py:

		urlpatterns = [
			*pages.maybe_list_page.page.get_urls(),
		]

	URL names follow the convention:
		- {name}.main_render
		- {name}.actions.{fn.__name__}
		- {name}.partials.{fn.__name__}
	"""

	def __init__(self, name, base_route):
		self.name = name
		self.base_route = base_route
		self._main = None  # (sub_route, fn)
		self._actions = []  # [(sub_route, route_override, method, fn)]
		self._partials = []  # [(sub_route, route_override, fn)]

	def main(self, fn_or_sub_route=None):
		"""
		Register the main GET render function.

		Can be used as:
			@page.main                  -> route = base_route
			@page.main('<str:kind>')    -> route = base_route/<str:kind>
		"""
		if callable(fn_or_sub_route):
			# @page.main without parens
			self._main = ('', fn_or_sub_route)
			return fn_or_sub_route

		# @page.main() or @page.main('<str:kind>')
		sub_route = fn_or_sub_route or ''

		def decorator(fn):
			self._main = (sub_route, fn)
			return fn

		return decorator

	def action(self, sub_route='', *, route=None, method='POST'):
		"""
		Register an action handler (POST by default).

		@page.action('create')                          -> POST base_route/create
		@page.action(route='models/project/do-thing')   -> POST models/project/do-thing
		@page.action('pdf', method='GET')               -> GET  base_route/pdf
		"""

		def decorator(fn):
			self._actions.append((sub_route, route, method, fn))
			return fn

		return decorator

	def partial(self, sub_route='', *, route=None):
		"""
		Register a GET HTMX partial handler.

		@page.partial('add-form')   -> GET base_route/add-form
		"""

		def decorator(fn):
			self._partials.append((sub_route, route, fn))
			return fn

		return decorator

	def _build_route(self, sub_route, route_override):
		if route_override is not None:
			return route_override
		if sub_route:
			return f'{self.base_route}/{sub_route}'
		return self.base_route

	def get_urls(self):
		urls = []

		# Actions and partials before main render, so that specific routes
		# are matched before a potentially catch-all main route (e.g. <str:kind>)
		for sub_route, route_override, method, fn in self._actions:
			http_decorator = require_GET if method == 'GET' else require_POST
			urls.append(
				path(
					route=self._build_route(sub_route, route_override),
					view=login_required(http_decorator(fn)),
					name=f'{self.name}.actions.{fn.__name__}',
				)
			)

		for sub_route, route_override, fn in self._partials:
			urls.append(
				path(
					route=self._build_route(sub_route, route_override),
					view=login_required(require_GET(fn)),
					name=f'{self.name}.partials.{fn.__name__}',
				)
			)

		if self._main:
			sub_route, fn = self._main
			urls.append(
				path(
					route=self._build_route(sub_route, None),
					view=login_required(require_GET(fn)),
					name=f'{self.name}.main_render',
				)
			)

		return urls
