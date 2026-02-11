# Conventions and best practices

## Folder organization

Unlike Django standard conventions, this app uses a different folder organization. This is mostly because I want to split the 
app into a logic business core, where all the models and logic are, and multiple presentation layers.

More precisely:
1. All the business logic is in the `core` folder
2. All the presentation logic is in the `apps` folder
3. The website is in the `apps/website` folder
4. The code relative to the Telegram bot is in the `apps/telegram` folder

## Page abstraction for views

Instead of standard Django views + `urlpatterns`, this project uses a `Page` class (`apps/website/pages/page.py`) that groups all views for a single page and generates URLs automatically.

Each page lives in its own module under `apps/website/pages/<name>/` with:
- `__init__.py` — re-exports from the module
- `<name>.py` — a `page` instance and view functions
- `<name>.html` — the main template (plus any partial templates)

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
    return render(request, 'task_list/add_form.html')
```

The `Page` class automatically applies `@login_required` and the correct HTTP method decorator (`@require_GET` / `@require_POST`) to all registered views. In `urls.py`, pages are registered by spreading `get_urls()`:

```python
urlpatterns = [
    *pages.task_list.page.get_urls(),
]
```

Key conventions:
1. Page names end with `_page` (e.g. `task_list_page`)
2. `@page.main` registers the main GET render, URL name: `{name}.main_render`
3. `@page.action(sub_route)` registers a POST handler, URL name: `{name}.actions.{fn_name}`
4. `@page.partial(sub_route)` registers a GET HTMX partial, URL name: `{name}.partials.{fn_name}`
5. Actions can override the HTTP method with `@page.action('pdf', method='GET')`
6. Routes can be fully overridden with the `route=` kwarg: `@page.action(route='models/project/do-thing')`
7. There are no views that accept both POST and GET