"""
Check the mechanical rules of CONVENTIONS.md.

	pipenv run python scripts/check_conventions.py
	pipenv run python scripts/check_conventions.py --update-baseline

Violations that predate this check are counted in scripts/conventions_baseline.txt, one line per
(rule, place). The check fails only when a place has more violations than its baseline allows.
"""

import ast
import re
import sys
from collections import Counter
from dataclasses import dataclass
from functools import partial
from itertools import chain
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / 'apps/website/pages'
COMPONENTS_DIR = ROOT / 'apps/website/components'
PYTHON_DIRS = ('apps', 'core')
FP_MODULE = 'core/utils/fp.py'
BASELINE = ROOT / 'scripts/conventions_baseline.txt'

PAGE_NAME = re.compile(r"Page\(\s*name='(?P<name>[^']+)'")
EXTENDS = re.compile(r'{%\s*extends\b')


@dataclass(frozen=True)
class Violation:
	rule: str
	place: str
	detail: str


type Counts = Counter[tuple[str, str]]


def relative(path: Path) -> str:
	return path.relative_to(ROOT).as_posix()


def page_layout_violations(page_dir: Path) -> list[Violation]:
	"""
	A page folder `<name>/` holds `__init__.py`, `<name>.py` and `<name>.html`, and its module registers
	`Page(name='<name>_page', ...)`.
	"""
	name = page_dir.name
	place = relative(page_dir)
	module = page_dir / f'{name}.py'

	def missing_file(file_name: str) -> Violation:
		return Violation('page-layout', place, f'missing {file_name}')

	def is_missing(file_name: str) -> bool:
		return not (page_dir / file_name).exists()

	missing = list(map(missing_file, filter(is_missing, ('__init__.py', f'{name}.py', f'{name}.html'))))

	if not module.exists():
		return missing

	registered = PAGE_NAME.search(module.read_text())
	if registered is None:
		return [*missing, Violation('page-name', place, f"no Page(name='{name}_page', ...) in {name}.py")]
	if registered['name'] != f'{name}_page':
		detail = f"Page name is '{registered['name']}', expected '{name}_page'"
		return [*missing, Violation('page-name', place, detail)]
	return missing


def partial_prefix_violations(template: Path) -> list[Violation]:
	"""
	A template that renders a fragment (no `{% extends %}`) is named `partial_*.html`; a template that
	extends a layout is not.
	"""
	place = relative(template)
	is_fragment = EXTENDS.search(template.read_text()) is None
	is_named_partial = template.name.startswith('partial_')

	if is_fragment and not is_named_partial:
		return [Violation('partial-prefix', place, 'renders a fragment but is not named partial_*.html')]
	if is_named_partial and not is_fragment:
		return [Violation('partial-prefix', place, 'extends a layout but is named partial_*.html')]
	return []


def is_list_of_map_or_filter(node: ast.AST) -> bool:
	return (
		isinstance(node, ast.Call)
		and isinstance(node.func, ast.Name)
		and node.func.id == 'list'
		and len(node.args) == 1
		and isinstance(node.args[0], ast.Call)
		and isinstance(node.args[0].func, ast.Name)
		and node.args[0].func.id in ('map', 'filter')
	)


def node_violation(module: Path, node: ast.AST) -> Violation | None:
	place = relative(module.parent)
	where = f'{relative(module)}:{getattr(node, "lineno", 0)}'

	if isinstance(node, ast.ListComp):
		return Violation('no-comprehension', place, f'{where}: list comprehension')
	if isinstance(node, ast.GeneratorExp):
		return Violation('no-comprehension', place, f'{where}: generator expression')
	if is_list_of_map_or_filter(node) and relative(module) != FP_MODULE:
		return Violation('use-lmap', place, f'{where}: list(map(...)) or list(filter(...))')
	return None


def python_violations(module: Path) -> list[Violation]:
	"""
	No list comprehensions or generator expressions, and `lmap` / `lfilter` instead of `list(map(...))` /
	`list(filter(...))`. Counted per folder, so renaming a module inside its folder changes nothing.
	"""
	nodes = ast.walk(ast.parse(module.read_text()))
	return sorted(filter(None, map(partial(node_violation, module), nodes)), key=lambda found: found.detail)


def all_violations() -> list[Violation]:
	def is_page_dir(path: Path) -> bool:
		return path.is_dir() and not path.name.startswith('_') and any(filter(Path.is_file, path.iterdir()))

	def python_modules(directory: str) -> list[Path]:
		return list(filter(lambda path: 'migrations' not in path.parts, (ROOT / directory).rglob('*.py')))

	page_dirs = sorted(filter(is_page_dir, PAGES_DIR.iterdir()))
	templates = sorted(chain(PAGES_DIR.rglob('*.html'), COMPONENTS_DIR.rglob('*.html')))
	modules = sorted(chain.from_iterable(map(python_modules, PYTHON_DIRS)))

	return list(
		chain(
			chain.from_iterable(map(page_layout_violations, page_dirs)),
			chain.from_iterable(map(partial_prefix_violations, templates)),
			chain.from_iterable(map(python_violations, modules)),
		)
	)


def read_baseline() -> Counts:
	def entry(line: str) -> tuple[tuple[str, str], int]:
		count, rule, place = line.split()
		return (rule, place), int(count)

	if not BASELINE.exists():
		return Counter()
	return Counter(dict(map(entry, filter(str.strip, BASELINE.read_text().splitlines()))))


def write_baseline(counts: Counts) -> None:
	lines = map(lambda item: f'{item[1]} {item[0][0]} {item[0][1]}', sorted(counts.items()))
	BASELINE.write_text('\n'.join(lines) + '\n')


def main() -> int:
	"""
	Compare the violations found in the codebase with the baseline. Returns the process exit code: 1 when
	some place has more violations than its baseline allows, 0 otherwise.
	"""
	violations = all_violations()
	counts: Counts = Counter(map(lambda found: (found.rule, found.place), violations))

	if '--update-baseline' in sys.argv:
		write_baseline(counts)
		print(f'Baseline updated: {len(violations)} known violations in {len(counts)} places.')
		return 0

	baseline = read_baseline()
	grown = sorted(filter(lambda key: counts[key] > baseline[key], counts))
	shrunk = sorted(filter(lambda key: counts[key] < baseline[key], baseline))

	for rule, place in grown:
		print(f'{rule}: {place} has {counts[rule, place]}, the baseline allows {baseline[rule, place]}')
		for found in filter(lambda found: (found.rule, found.place) == (rule, place), violations):
			print(f'    {found.detail}')

	for rule, place in shrunk:
		print(f'note: {rule} in {place} is down from {baseline[rule, place]} to {counts[rule, place]}')

	if shrunk:
		print('note: lock the progress in with --update-baseline')

	if grown:
		print('\nConventions check failed. The rules are in CONVENTIONS.md.')
		return 1

	print(f'Conventions check passed ({len(violations)} known violations remain).')
	return 0


if __name__ == '__main__':
	sys.exit(main())
