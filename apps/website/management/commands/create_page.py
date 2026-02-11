import os
from pathlib import Path
from textwrap import dedent

from django.core.management.base import BaseCommand

PAGES_DIR = Path('apps/website/pages')
PAGES_INIT = PAGES_DIR / '__init__.py'
URLS_FILE = Path('apps/website/urls.py')


def build_page_init(name):
	return f'from .{name} import *\n'


def build_page_module(name, base_route):
	return dedent(f"""\
		from django.shortcuts import render

		from apps.website.pages.page import Page

		page = Page(name='{name}_page', base_route='{base_route}')


		@page.main
		def main_render(request):
		\treturn render(request, '{name}/{name}.html')
	""")


def build_page_template(name):
	return dedent(f"""\
		{{% extends 'base.html' %}}

		{{% block content %}}
		<h1>{name}</h1>
		{{% endblock %}}
	""")


def patch_pages_init(name, content):
	lines = content.splitlines(keepends=True)

	# Find the closing ')' of the 'from . import (...)' block and insert before it
	import_insert_idx = next(i for i, line in enumerate(lines) if line.strip() == ')')
	lines.insert(import_insert_idx, f'\t{name},\n')

	# Find the closing ']' of __all__ and insert before it
	all_insert_idx = next(i for i, line in enumerate(lines) if line.strip() == ']')
	lines.insert(all_insert_idx, f"\t'{name}',\n")

	return ''.join(lines)


def patch_urls(name, content):
	marker = '] + static('
	return content.replace(marker, f'\t*pages.{name}.page.get_urls(),\n{marker}')


class Command(BaseCommand):
	help = 'Scaffold a new page under apps/website/pages/'

	def add_arguments(self, parser):
		parser.add_argument('name', type=str, help='Page module name (e.g. task_list)')
		parser.add_argument('base_route', type=str, help='URL base route (e.g. pages/tasks)')

	def handle(self, *args, **options):
		name = options['name']
		base_route = options['base_route']
		page_dir = PAGES_DIR / name

		if page_dir.exists():
			self.stderr.write(self.style.ERROR(f'Directory already exists: {page_dir}'))
			return

		# Create page directory and files
		os.makedirs(page_dir)
		created = []

		init_path = page_dir / '__init__.py'
		init_path.write_text(build_page_init(name))
		created.append(init_path)

		module_path = page_dir / f'{name}.py'
		module_path.write_text(build_page_module(name, base_route))
		created.append(module_path)

		template_path = page_dir / f'{name}.html'
		template_path.write_text(build_page_template(name))
		created.append(template_path)

		# Patch pages/__init__.py
		pages_init_content = PAGES_INIT.read_text()
		PAGES_INIT.write_text(patch_pages_init(name, pages_init_content))

		# Patch urls.py
		urls_content = URLS_FILE.read_text()
		URLS_FILE.write_text(patch_urls(name, urls_content))

		self.stdout.write(self.style.SUCCESS('Created:'))
		for path in created:
			self.stdout.write(f'  {path}')
		self.stdout.write(self.style.SUCCESS('Modified:'))
		self.stdout.write(f'  {PAGES_INIT}')
		self.stdout.write(f'  {URLS_FILE}')
