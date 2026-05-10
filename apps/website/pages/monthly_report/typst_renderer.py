"""
Render a `MonthlyReport` into a PDF using the Typst typesetting engine.

The Typst document is built as a string in Python and compiled in-process via
the official `typst` Python package (which embeds the Rust compiler — no system
binary, no external network calls, no Typst package fetches).

Charts are rendered to PNG with matplotlib (see `charts.py`) and embedded
as images via Typst's `#image(...)` so the PDF gets a real chart toolkit's
output instead of hand-drawn boxes.
"""

import calendar
import tempfile
from pathlib import Path

import typst

from apps.website.pages.monthly_report import charts

MONTH_NAMES = [
	'',
	'January',
	'February',
	'March',
	'April',
	'May',
	'June',
	'July',
	'August',
	'September',
	'October',
	'November',
	'December',
]

FOOD_CHART_WIDTH_IN = 6.6
FOOD_CHART_TYPST_WIDTH = '17cm'


class _AssetWriter:
	"""Writes auxiliary chart files into the typst compile directory and returns their filenames."""

	def __init__(self, directory: Path):
		self._directory = directory
		self._counter = 0

	def write_svg(self, svg_bytes: bytes) -> str:
		self._counter += 1
		filename = f'chart-{self._counter}.svg'
		(self._directory / filename).write_bytes(svg_bytes)
		return filename


def _month_label(year, month, short=False):
	name = calendar.month_abbr[month] if short else MONTH_NAMES[month]
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


def total_section(report):

	return f"""\
== Total monthly expense: {_money_mono(report.month_total)}
"""


def _render_food_scatter_section(report, writer):
	"""Scatter chart of groceries / eat-out / delivery transactions over the preceding 12 months."""
	month_label = _month_label(report.year, report.month)
	svg = charts.food_scatter_svg(
		report.food_transactions, report.year, report.month, width_in=FOOD_CHART_WIDTH_IN
	)
	filename = writer.write_svg(svg)
	return f"""\
== Food spending trends
#image({_typst_string(filename)}, width: {FOOD_CHART_TYPST_WIDTH})
"""


def _render_transactions_table(report):
	if not report.transactions:
		return '== All expenses\n\nNo transactions recorded for this month.\n'

	body_rows = '\n'.join(
		f'  {_typst_string(t.date.isoformat())}, {_typst_string(t.description)}, '
		f'{_typst_string(t.category_name)}, [{_money_mono(t.amount)}],'
		for t in report.transactions
	)

	# Header row in `#e0e0e0`, body rows in `#f0f0f0`, with white 1pt strokes between cells —
	# mirrors the website table aesthetic (`tables.css`).
	return f"""\
== All expenses

#table(
  columns: (auto, 1fr, auto, auto),
  align: (left, left, left, right),
  stroke: 1pt + white,
  inset: (x: 6pt, y: 4pt),
  fill: (_, row) => if row == 0 {{ rgb("#e0e0e0") }} else {{ rgb("#f0f0f0") }},
  [*Date*], [*Description*], [*Category*], [*Amount*],
{body_rows}
)
"""


def _build_typst_source(report, writer):
	"""Build the Typst source document, writing chart PNG assets via `writer` as a side effect."""

	month_label = _month_label(report.year, report.month)

	return f"""\
#set page(paper: "a4", margin: 1.6cm)
#set text(font: ("Public Sans", "American Typewriter", "Linux Libertine"), size: 10pt, fill: rgb("#1a1a1a"))
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

{total_section(report)}
{_render_food_scatter_section(report, writer)}
{_render_transactions_table(report)}
"""


def render_report_pdf(report) -> bytes:
	"""Compile the report to PDF bytes."""
	with tempfile.TemporaryDirectory() as tmp:
		tmp_path = Path(tmp)
		writer = _AssetWriter(tmp_path)
		source = _build_typst_source(report, writer)
		typ_path = tmp_path / 'report.typ'
		typ_path.write_text(source, encoding='utf-8')
		return typst.compile(str(typ_path))
