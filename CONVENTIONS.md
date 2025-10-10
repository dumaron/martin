# Conventions and best practices

## Folder organization

Unlike Django conventions, this app uses a different folder organization. This is mostly because I want to split the 
app into a logic business core, where all the models and logic are, and multiple presentation layers.

More precisely:
1. All the business logic is in the `core` folder
2. All the presentation logic is in the `apps` folder
3. The website is in the `apps/website` folder
4. The code relative to the Telegram bot is in the `apps/telegram` folder

## Multiple presentation layers

Unlike most Django apps, this app has multiple presentation layers. Basically I am reusing Django's ORM and admin utilities
to build an application that interfaces in many ways with the user (me). Right now there is a website and a Telegram bot,
but I plan to add more in the future. Maybe some APIs, that will be considered separated from the website.

This means the code must not assume that everything is about web pages. It must be designed to be easily extensible to
new presentation layers.
