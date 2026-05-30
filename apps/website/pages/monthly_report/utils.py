import calendar


def category_label(ynab_category):
	if ynab_category is None:
		return 'Uncategorized'
	if ynab_category.category_group_name == 'Olmo':
		return f'Olmo→{ynab_category.name}'

	return ynab_category.name


def month_label(year, month, short=False):
	name = calendar.month_abbr[month] if short else calendar.month_name[month]
	return f'{name} {year}'


def typst_string(s):
	"""Escape a Python string to a Typst string literal."""
	if s is None:
		return '""'
	escaped = (
		str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
	)
	return f'"{escaped}"'


def money(value):
	"""Format a numeric value as a plain string, e.g. `1 234.56 €`."""
	whole, _, frac = f'{value:,.2f}'.partition('.')
	whole = whole.replace(',', ' ')
	return f'{whole}.{frac} €'


def mono(string: str) -> str:
	"""Format a string as a monospace font."""
	return f'#text(font: ("Berkeley Mono", "DejaVu Sans Mono"))[{typst_string(string)}]'
