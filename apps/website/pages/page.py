import re
from collections.abc import Sequence
from itertools import product

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.http import require_GET, require_POST

from core.utils.fp import lmap

# An optional path parameter: Django's own `<converter:name>` with a `?` pinned to the converter.
# Django has no optional-parameter syntax — `path()` would reject `int?` as an unknown converter — so we
# expand these ourselves into one concrete route per present/absent combination.
_OPTIONAL_PARAMETER_RE = re.compile(r'^<(?P<converter>[^>:]+)\?:(?P<parameter>[^>:]+)>$')


def _to_required(segment):
	return _OPTIONAL_PARAMETER_RE.sub(r'<\g<converter>:\g<parameter>>', segment)


def _expand_optional_params(route):
	"""
	Turn a route with optional parameters into the concrete Django routes it stands for.

		'knowledge/add/<int?:transaction_id>'       -> ['knowledge/add/<int:transaction_id>', 'knowledge/add']
		'knowledge/add/<int?:transaction_id>/save'  -> ['knowledge/add/<int:transaction_id>/save',
		                                                'knowledge/add/save']

	Most specific first. An optional parameter has to be a whole path segment (the slash that would be left
	dangling is dropped with it), and the view must give the argument a default, since the shorter route
	calls it without.
	"""
	segments = route.split('/')
	optional_indexes = [index for index, segment in enumerate(segments) if _OPTIONAL_PARAMETER_RE.match(segment)]
	if not optional_indexes:
		return [route]

	def build(dropped):
		kept = [segment for index, segment in enumerate(segments) if index not in dropped]
		return '/'.join(lmap(_to_required, kept))

	# `product` yields the all-present combination first, so longer routes are registered before shorter ones.
	return lmap(
		lambda keeps: build({index for index, keep in zip(optional_indexes, keeps) if not keep}),
		product([True, False], repeat=len(optional_indexes)),
	)


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

	Any route may use an optional parameter, written as Django's `<converter:name>` with a `?` on the
	converter. It registers several patterns under the single name above, and `reverse` picks whichever one
	matches the arguments it is handed:

		@page.main('<int?:transaction_id>')   -> GET base_route  and  base_route/<int:transaction_id>

		reverse('item_page.main_render')                     -> /items
		reverse('item_page.main_render', args=[7])           -> /items/7

	The view has to default the argument (`def main_render(request, transaction_id=None)`), because the
	shorter pattern calls it without.

	A view may also provide multiple routes with different shapes. They share the same URL name, and `reverse`
	selects the pattern matching the supplied arguments:

		@page.main(['new', '<int:transaction_id>/edit'])
		def main_render(request, transaction_id=None):
			...
	"""

	def __init__(self, name, base_route):
		self.name = name
		self.base_route = base_route
		self._main = []  # [(sub_route, fn)]
		self._actions = []  # [(sub_route, route_override, method, fn)]
		self._partials = []  # [(sub_route, route_override, fn)]

	def main(self, fn_or_sub_routes=None):
		"""
		Register the main GET render function.

		Can be used as:
			@page.main                                      -> route = base_route
			@page.main('<str:kind>')                        -> route = base_route/<str:kind>
			@page.main(['new', '<int:item_id>/edit'])       -> register both routes
		"""
		if callable(fn_or_sub_routes):
			# @page.main without parens
			self._main.append(('', fn_or_sub_routes))
			return fn_or_sub_routes

		if fn_or_sub_routes is None:
			sub_routes = ('',)
		elif isinstance(fn_or_sub_routes, str):
			sub_routes = (fn_or_sub_routes,)
		elif isinstance(fn_or_sub_routes, Sequence):
			sub_routes = tuple(fn_or_sub_routes)
			if not sub_routes:
				raise ValueError('Page.main requires at least one route')
			if not all(isinstance(sub_route, str) for sub_route in sub_routes):
				raise TypeError('Page.main routes must be strings')
		else:
			raise TypeError('Page.main expects a route string or a sequence of route strings')

		def decorator(fn):
			self._main.extend((sub_route, fn) for sub_route in sub_routes)
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

	def _paths(self, route, view, name):
		# A single registration yields more than one Django route when it uses optional parameters. They all
		# share the same URL name, which `reverse` handles by trying each pattern against the given arguments.
		return lmap(
			lambda expanded: path(route=expanded, view=view, name=name),
			_expand_optional_params(route),
		)

	def get_urls(self):
		urls = []

		# Actions and partials before main render, so that specific routes
		# are matched before a potentially catch-all main route (e.g. <str:kind>)
		for sub_route, route_override, method, fn in self._actions:
			http_decorator = require_GET if method == 'GET' else require_POST
			urls.extend(
				self._paths(
					route=self._build_route(sub_route, route_override),
					view=login_required(http_decorator(fn)),
					name=f'{self.name}.actions.{fn.__name__}',
				)
			)

		for sub_route, route_override, fn in self._partials:
			urls.extend(
				self._paths(
					route=self._build_route(sub_route, route_override),
					view=login_required(require_GET(fn)),
					name=f'{self.name}.partials.{fn.__name__}',
				)
			)

		for sub_route, fn in self._main:
			urls.extend(
				self._paths(
					route=self._build_route(sub_route, None),
					view=login_required(require_GET(fn)),
					name=f'{self.name}.main_render',
				)
			)

		return urls
