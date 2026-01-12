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

There is an implicit "page" abstraction in place which shapes views and urls. Here is how the abstraction is defined:
1. Every page on the web app is one "page" in the application, represented by a single file in the `views` folder
2. Every Django URL name for a page ends with `_page`, and then is followed by some specific identifier, like `project_detail_page.something.something`
3. There is a `main_render` view function for each page, which requires GET method and renders the page
4. Django URL name for `main_render` is `page_name.main_render`, like `project_detail_page.main_render`
5. Every possible form submission in that page is an "action", which is a POST method call to different view function in the same file
6. Django URL name for an action is `page_name.actions.action_name`
7. There are no methods that are both POST and GET
8. View functions for HTMX partials have URL names like `page_name.partials.partial_name`
9. There might be secondary views, like one for getting a PDF; in this case, the URL name is `page_name.secondary_views.secondary_view_name`