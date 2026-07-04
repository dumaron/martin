import calendar
from datetime import date

REPORT_WINDOW_MONTHS = 7  # target month + 6 preceding


def _add_months(year, month, delta):
	"""First of the month `delta` months away from (year, month). `delta` may be negative."""
	total = (year * 12 + (month - 1)) + delta
	y, m = divmod(total, 12)
	return date(y, m + 1, 1)


def report_window(year, month):
	"""(start, end) date bounds for the report window; `end` is exclusive (first of the
	month after `month`)."""
	start = _add_months(year, month, -(REPORT_WINDOW_MONTHS - 1))
	end = _add_months(year, month, 1)
	return start, end


def report_month_starts(year, month):
	"""First-of-month dates across the report window (oldest first), with the exclusive
	right boundary appended as the final entry — chart code uses it to compute the last
	band's midpoint."""
	start, end = report_window(year, month)
	starts = list(map(lambda i: _add_months(start.year, start.month, i), range(REPORT_WINDOW_MONTHS)))
	return starts + [end]


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
	return f'#text(font: ("Berkeley Mono", "DejaVu Sans Mono"), {typst_string(string)})'
