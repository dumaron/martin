# Conventions and best practices

## Folder organization

Unlike Django standard conventions, this app uses a different folder organization. This is mostly because I want to split the 
app into a logic business core, where all the models and logic are, and multiple presentation layers.

More precisely:
1. All the business logic is in the `core` folder
2. All the presentation logic is in the `apps` folder
3. The website is in the `apps/website` folder
4. The code relative to the Telegram bot is in the `apps/telegram_bot` folder

## Page abstraction for views

Instead of standard Django views + `urlpatterns`, this project uses a `Page` class (`apps/website/pages/page.py`) that groups all views for a single page and generates URLs automatically.

Each page lives in its own module under `apps/website/pages/<name>/` with:
- `__init__.py` — re-exports from the module
- `<name>.py` — a `page` instance and view functions
- `<name>.html` — the main template
- `partial_<what>.html` — any partial template (see [Template partials](#template-partials))

A page module creates a `Page` instance and registers views with decorators:

```python
page = Page(name='task_list_page', base_route='pages/tasks')

@page.main
def main_render(request):
    return render(request, 'task_list/task_list.html')

@page.action('create')
def create(request):
    ...

@page.partial('add-form')
def add_form(request):
    return render(request, 'task_list/partial_add_form.html')
```

The `Page` class automatically applies `@login_required` and the correct HTTP method decorator (`@require_GET` / `@require_POST`) to all registered views. In `urls.py`, pages are registered by spreading `get_urls()`:

```python
urlpatterns = [
    *pages.task_list.page.get_urls(),
]
```

Key conventions:
1. The page name is the folder name plus `_page`: the page in `pages/task_list/` is `Page(name='task_list_page', ...)`
2. `@page.main` registers the main GET render, URL name: `{name}.main_render`
3. `@page.action(sub_route)` registers a POST handler, URL name: `{name}.actions.{fn_name}`
4. `@page.partial(sub_route)` registers a GET HTMX partial, URL name: `{name}.partials.{fn_name}`
5. Actions can override the HTTP method with `@page.action('pdf', method='GET')`
6. Routes can be fully overridden with the `route=` kwarg: `@page.action(route='models/project/do-thing')`
7. There are no views that accept both POST and GET

### Template partials

A partial is a template that renders a fragment instead of a whole page: it is pulled in with `{% include %}`, or returned to HTMX by a `@page.partial` or an action. A partial never `{% extends %}` another template.

Under `apps/website/pages/` and `apps/website/components/`:
1. Every partial is named `partial_<what>.html` (e.g. `partial_fact_row.html`)
2. Never use a leading underscore (`_fact_row.html`) or no prefix at all (`fact_row.html`)
3. A template that does `{% extends %}` a layout is a page, and never takes the prefix

### Validating action input

Views receive raw strings from `request.POST` / `request.GET`. Validate the raw value *before* casting it, and reject bad input explicitly by returning `HttpResponseBadRequest('<message>')` — never let a cast decide the outcome, and never silently skip the work and redirect as if it succeeded.

```python
rating = request.POST.get('rating')
if rating not in ('1', '2', '3', '4'):
    return HttpResponseBadRequest('Invalid flashcard rating')

review_flashcard(flashcard, int(rating))
```

Casting first (`int(request.POST.get('rating'))`) turns a missing or non-numeric field into a `TypeError` / `ValueError` and a 500. Guarding with `if value in (...): do_work()` and falling through to the redirect hides the failure from the user, who just sees the unchanged page.

For anything beyond a couple of fields, use a Django `Form` and return `HttpResponseBadRequest('Invalid form data')` when `form.is_valid()` fails — see `create_ynab_transaction` in `apps/website/pages/pair_transactions/pair_transactions.py`. Object lookups keep using `get_object_or_404`.

## Components

A piece of UI that is shown in more than one pages does not belong to them, so it lives in
`apps/website/components/<name>/` rather than under `apps/website/pages/`: the Python module and its
`partial_*.html`. That directory is on the template search path, so a page includes it as
`{% include "<name>/partial_<name>.html" %}`. The CSS stays in `apps/website/static/styles/` with every
other stylesheet.

A component is markup plus the helper a view uses to build its context. It registers no routes of its own:
an action belongs to the page that triggers it, duplicated across pages if need be.

### Quick links

A page can offer a "Quick links" section: a short list of places worth going next from here. It belongs in
the right-hand `.secondary-content` column, next to sidebars and suggestion panels, not in the main
`.fixed-content` flow. The section is one shared partial, so every page that has one looks the same and
gains new entries by touching only its view.

Build the entries with `quick_link` (`apps/website/components/quick_links/quick_links.py`) and put them in the context under
`quick_links`:

```python
from apps.website.components.quick_links import quick_link

@page.main
def main_render(request, project_id):
	...
	return render(request, 'project_detail/project_detail.html', {
		...,
		'quick_links': [
			quick_link('Add another root project', 'project_create_page.main_render'),
			quick_link('Go to project work tree', 'project_work_tree_page.main_render'),
		],
	})
```

Then include the partial in the page's secondary column — it reads `quick_links` straight from the context
and renders nothing when the list is missing or empty:

```html
    </div>
    <div class="secondary-content">
        {% include "quick_links/partial_quick_links.html" %}
    </div>
{% endblock %}
```

## Python style

### Use `lmap` / `lfilter` instead of comprehensions

This codebase favors functional-style sequence transformations. Do not write list comprehensions (`[f(x) for x in xs]`) or generator expressions (`(f(x) for x in xs)`). Use the helpers exported by `core/utils/fp.py` instead:

```python
from core.utils.fp import concat, lfilter, lmap
```

| Avoid                                              | Write                                               |
|----------------------------------------------------|-----------------------------------------------------|
| `[f(x) for x in xs]`                               | `lmap(f, xs)`                                       |
| `[x for x in xs if pred(x)]`                       | `lfilter(pred, xs)`                                 |
| `[f(x) for x in xs if pred(x)]`                    | `lmap(f, filter(pred, xs))`                         |
| `[f(x) for xs in xss for x in xs]`                 | `lmap(f, concat(xss))`                              |
| `[x for x in iterable]` (pure materialisation)     | `list(iterable)`                                    |
| `list(map(f, xs))`                                 | `lmap(f, xs)`                                       |
| `list(filter(pred, xs))`                           | `lfilter(pred, xs)`                                 |
| `any(pred(x) for x in xs)`                         | `any(map(pred, xs))`                                |
| `', '.join(f(x) for x in xs)`                      | `', '.join(map(f, xs))`                             |

`lmap` and `lfilter` return a list. When the consumer already accepts any iterable — e.g. `str.join`, `sum`, `any`, `all`, `set`, `tuple`, `bulk_create`, or a spread such as `[first, *map(f, xs)]` — pass the lazy builtin `map` / `filter` instead: `', '.join(map(f, xs))`, not `', '.join(lmap(f, xs))`.

Where the rule applies:
1. `apps/` and `core/`, tests included
2. Not `scripts/`: those files run standalone and cannot import `core`
3. Not dict comprehensions (`{k: v for ...}`) and set comprehensions (`{x for ...}`), which remain idiomatic and are unchanged

### Use `pipe` for three or more chained transformations

When one value goes through three or more transformations in a row, write the chain with `pipe` (exported by `core/utils/fp.py`): the value first, then one step per line, using the curried helpers (`lmap(f)`, `lfilter(pred)`) as steps.

```python
return pipe(
	rows,
	lmap(Row.terms),
	concat,
	lfilter(lambda term: term.is_variable),
)
```

With one or two transformations, nest the calls or name an intermediate variable. `pipe` only adds noise there:

```python
return lmap(parse_row, filter(has_content, lines))
```

Do not use `pipe` when the steps are not a straight line: when a later step needs an earlier intermediate result, or when the flow branches.

### An example piece of code I'm proud of

```python
### FILLING QUERY VARIABLES FROM RESULTS ###

type Result = dict[str, str | None]  # variable name (no `$`) -> value, None if an optional row didn't match
type Fact = tuple[str, str, str]  # (subject, predicate, object)


def matched_facts(query: str, results: list[Result]) -> list[Fact]:
	"""
	Return the distinct facts behind the given results.
	Each query row is filled with each result's values; optional rows that didn't match are dropped.
	"""

	def bound(term: Term, result: Result) -> str | None:
		return result[term.text] if term.is_variable else term.text

	def bound_fact(pair: tuple[Result, Row]) -> tuple[str | None, str, str | None]:
		result, row = pair
		return bound(row.subject, result), row.predicate, bound(row.object, result)

	drop_optionals_missing_matches = lfilter(lambda fact: None not in fact)

	return pipe(
		product(results, parse(query)),  # Iterator[tuple[Result, Row]]
		lmap(bound_fact),  #               list[tuple[str | None, str, str | None]]
		drop_optionals_missing_matches,  # list[Fact]
		lunique,  #                        list[Fact]
	)

```

In the piece of code above you can find many interesting elements that, composed together, creates readable code - at least for my eyes. And in this codebase we're maximizing readability for only one user - myself.

- variables and functions are typed
- function names can be long, if it helps to explain what they do
- helper functions are welcome, but they should not pollute the main scope if they're used only to make a function more readable
- main functions should be commented
- some additional types are welcome if they make function safer and easier to read, but they should be close to the functions that requires them
- inline function definition thanks to currying is welcome, actually encouraged (look at `drop_optionals_missing_matches`)
- `pipe` used because three transformations are chained: it helps me see how we're basically chaining a set of transformations on top of the input
- the comments for types are optional, but they made it easier for me to grasp the transformations since I'm still confused by Python's data structures

## PDF reports
PDF reports are generated via typst. The example report is `apps/website/pages/monthly_report/report_renderer.py`.

A few notes on them:
- There is a header, and then every report is composed of "sections", which are implemented by python functions returning
    a typst string
- Every report starts by fetching all the data it needs from the database; it is up to every section to filter / manipulate
    the big set of data as needed

## Checking the conventions

`scripts/check_conventions.py` checks the rules a script can decide, and CI runs it on every pull request:

```
pipenv run python scripts/check_conventions.py
```

What it checks:
1. Every folder in `apps/website/pages/` has `__init__.py`, `<name>.py` and `<name>.html`
2. Every page module registers `Page(name='<name>_page', ...)`
3. Templates in `apps/website/pages/` and `apps/website/components/` follow the [Template partials](#template-partials) naming
4. `apps/` and `core/` contain no list comprehension, no generator expression, and no `list(map(...))` / `list(filter(...))`

Violations older than the check are counted in `scripts/conventions_baseline.txt`, one line per rule and place. The check fails only when a place has more violations than its baseline line allows, so never add a violation and never raise a count by hand. After fixing old violations, lower the counts with:

```
pipenv run python scripts/check_conventions.py --update-baseline
```
