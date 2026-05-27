import calendar
import tempfile
from pathlib import Path

import typst

from apps.website.pages.monthly_report import charts
from core.constants import FOOD_YNAB_GROUP_CATEGORY_NAME
from core.models import BankTransaction


### UTILS ###
def _month_label(year, month, short=False):
	name = calendar.month_abbr[month] if short else calendar.month_name[month]
	return f'{name} {year}'


def _typst_string(s):
	"""Escape a Python string to a Typst string literal."""
	if s is None:
		return '""'
	escaped = (
		str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
	)
	return f'"{escaped}"'


def _money(value):
	"""Format a numeric value as a plain string, e.g. `1 234.56 €`."""
	whole, _, frac = f'{value:,.2f}'.partition('.')
	whole = whole.replace(',', ' ')
	return f'{whole}.{frac} €'


def _money_mono(value):
	"""Format a numeric value as a Typst content block in the monospace amount style."""
	return f'#text(font: ("Berkeley Mono", "DejaVu Sans Mono"))[{_money(value)}]'


def total_section(year, month, transactions):
	target_month_txns = filter(lambda t: t.date.year == year and t.date.month == month, transactions)
	total = sum(map(lambda t: t.amount, target_month_txns))
	return f"""\
== Total monthly expense: {total}
"""


def food_transactions_only(all_transactions):
	return list(
		filter(
			lambda t: t.matched_ynab_transaction.category
			and t.matched_ynab_transaction.category.category_group_name == FOOD_YNAB_GROUP_CATEGORY_NAME,
			all_transactions,
		)
	)


### REPORT SECTIONS ###


def food_scatter_section(year, month, all_transactions, tmp_path) -> str:
	"""TODO add description"""
	svg = charts.food_scatter_svg(food_transactions_only(all_transactions), year, month)
	svg_filename = 'food_scatter.svg'
	(tmp_path / svg_filename).write_bytes(svg)
	return f"""\
== Food spending trends
#image("{svg_filename}", width: 17cm)
"""


def food_totals_section(year, month, all_transactions, tmp_path) -> str:
	"""TODO add description"""

	svg = charts.food_totals_svg(food_transactions_only(all_transactions), year, month)
	svg_filename = 'food_totals.svg'
	(tmp_path / svg_filename).write_bytes(svg)
	return f"""\
== Food spending — monthly totals
#image("{svg_filename}", width: 17cm)
"""


def expenses_totals_section(year, month, all_transactions, tmp_path) -> str:
	svg = charts.expenses_totals_svg(all_transactions, year, month)
	svg_filename = 'expenses_totals.svg'
	(tmp_path / svg_filename).write_bytes(svg)
	return f"""\
== All expenses — monthly totals
#image("{svg_filename}", width: 17cm)
"""


def category_totals_section(year, month, all_transactions, tmp_path) -> str:
	svg = charts.category_totals_svg(all_transactions, year, month)
	svg_filename = 'category_totals.svg'
	(tmp_path / svg_filename).write_bytes(svg)
	return f"""\
== Expenses by category
#image("{svg_filename}", width: 17cm)
"""


def all_expenses_section(all_transactions, month):
	last_month_transactions = filter(lambda t: t.date.month == month, all_transactions)
	sorted_by_amount = sorted(last_month_transactions, key=lambda t: abs(t.amount), reverse=True)

	body_rows = '\n'.join(
		f'  {_typst_string(t.date.isoformat())}, {_typst_string(t.matched_ynab_transaction.memo)}, '
		f'{_typst_string(t.matched_ynab_transaction.category.name if t.matched_ynab_transaction.category else "")}, '
		f'[{_money_mono(t.amount)}],'
		for t in sorted_by_amount
	)

	row_separator_stroke = '(_, y) => if y > 0 { (top: 0.5pt + rgb("#cccccc")) }'
	return f"""\
== All expenses

#table(
  columns: (auto, 1fr, auto, auto),
  align: (left, left, left, right),
  stroke: {row_separator_stroke},
  inset: (x: 6pt, y: 4pt),
  [*Date*], [*Description*], [*Category*], [*Amount*],
{body_rows}
)
"""


def report_header(month_label: str) -> str:
	return f"""
	#set page(paper: "a4", margin: 1.6cm)
	#set text(font: ("Public Sans", "American Typewriter", "Linux Libertine"), size: 9pt, fill: rgb("#1a1a1a"))
	#set par(justify: false)
	#show heading.where(level: 1): it => block(below: 0.8em)[
	  #set text(size: 20pt, weight: "bold")
	  #it.body
	  #v(-0.3em)
	  #line(length: 100%, stroke: 0.8pt + rgb("#1a1a1a"))
	]
	#show heading.where(level: 2): set text(size: 14pt, weight: "bold")
	#show heading.where(level: 3): set text(size: 11pt, weight: "bold")
	#show link: set text(fill: blue)

	= Monthly expense report — {month_label}

	_Shared bank account_
	"""


def shared_expenses_account_monthly_report(year, month, tmp_path):
	_m = month - 6
	start = f'{year - 1}-{_m + 12:02d}-01' if _m <= 0 else f'{year}-{_m:02d}-01'
	_nm = month + 1
	end = f'{year + 1}-01-01' if _nm > 12 else f'{year}-{_nm:02d}-01'

	month_label = _month_label(year, month)
	all_transactions_in_time_window = list(
		BankTransaction.objects.filter(
			bank_account__personal=False,
			matched_ynab_transaction__isnull=False,
			matched_ynab_transaction__transfer_account_id__isnull=True,
			amount__lt=0,
			date__gte=start,
			date__lt=end,
			# The deepest path implies the shallower one: this single JOIN populates both
			# `t.matched_ynab_transaction` and `t.matched_ynab_transaction.category`.
		).select_related('matched_ynab_transaction__category')
	)

	return f"""
{report_header(month_label)}
{total_section(year, month, all_transactions_in_time_window)}
{expenses_totals_section(year, month, all_transactions_in_time_window, tmp_path)}
{category_totals_section(year, month, all_transactions_in_time_window, tmp_path)}
{food_totals_section(year, month, all_transactions_in_time_window, tmp_path)}
{food_scatter_section(year, month, all_transactions_in_time_window, tmp_path)}
{all_expenses_section(all_transactions_in_time_window, month)}
"""


def render_report_pdf(year, month) -> bytes | list[bytes] | None:
	"""Compile the report to PDF bytes."""
	with tempfile.TemporaryDirectory() as tmp:
		tmp_path = Path(tmp)
		source = shared_expenses_account_monthly_report(year, month, tmp_path)
		typ_path = tmp_path / 'report.typ'
		typ_path.write_text(source, encoding='utf-8')
		return typst.compile(str(typ_path))
