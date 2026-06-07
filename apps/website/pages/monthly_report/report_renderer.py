import typst

from apps.website.pages.monthly_report import charts
from core.constants import FOOD_YNAB_GROUP_CATEGORY_NAME
from core.models import BankTransaction
from settings import FONTS_DIR

from .utils import category_label, money, mono, month_label, report_window, typst_string


def total_section(year, month, transactions):
	target_month_txns = filter(lambda t: t.date.year == year and t.date.month == month, transactions)
	total = sum(map(lambda t: abs(t.amount), target_month_txns))
	return f"""\
== Total monthly expense: {money(total)}
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


# I mean, let's be honest: wouldn't it be way more elegant with some sort of component system like JSX?
def chart_container(title, svg) -> str:
	svg_literal = '"' + svg.decode('utf-8').replace('\\', '\\\\').replace('"', '\\"') + '"'

	return f"""\
== {title}
#align(center)[#image(bytes({svg_literal}), format: "svg", width: 15cm)]
#v(1cm, weak: true)
"""


def food_scatter_section(year, month, all_transactions) -> str:
	svg = charts.food_scatter_svg(food_transactions_only(all_transactions), year, month)
	return chart_container('Food spending trends', svg)


def food_totals_section(year, month, all_transactions) -> str:
	svg = charts.food_totals_svg(food_transactions_only(all_transactions), year, month)
	return chart_container('Food spending — monthly totals', svg)


def expenses_totals_section(year, month, all_transactions) -> str:
	svg = charts.expenses_totals_svg(all_transactions, year, month)
	return chart_container('All expenses — monthly totals', svg)


def category_totals_section(year, month, all_transactions) -> str:
	svg = charts.category_totals_svg(all_transactions, year, month)
	return chart_container('Expenses by category', svg)


def all_expenses_section(all_transactions, year, month):
	last_month_transactions = filter(lambda t: t.date.year == year and t.date.month == month, all_transactions)
	sorted_by_amount = sorted(last_month_transactions, key=lambda t: abs(t.amount), reverse=True)

	# God I miss the pipe operator
	cell_extractors = [
		lambda t: typst_string(t.date.isoformat()),
		lambda t: typst_string(t.matched_ynab_transaction.memo),
		lambda t: typst_string(category_label(t.matched_ynab_transaction.category)),
		lambda t: f'[{mono(money(t.amount))}]',
	]

	def expense_row(t):
		return '  ' + ', '.join(extract(t) for extract in cell_extractors) + ','

	body_rows = '\n'.join(map(expense_row, sorted_by_amount))

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


def shared_expenses_account_monthly_report(year, month):
	start, end = report_window(year, month)

	transactions = list(
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

	sections = [
		report_header(month_label(year, month)),
		total_section(year, month, transactions),
		expenses_totals_section(year, month, transactions),
		category_totals_section(year, month, transactions),
		food_totals_section(year, month, transactions),
		food_scatter_section(year, month, transactions),
		all_expenses_section(transactions, year, month),
	]
	return '\n'.join(sections)


def render_report_pdf(year, month) -> bytes | list[bytes] | None:
	source = shared_expenses_account_monthly_report(year, month)
	# Typst only auto-discovers system fonts; on the server "Public Sans" lives in
	# FONTS_DIR (/storage/fonts), so it must be passed explicitly as a font path.
	return typst.compile(source.encode('utf-8'), font_paths=[FONTS_DIR])
