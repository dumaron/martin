"""
Matplotlib chart helpers used by the monthly expense report.

Functions return SVG bytes; the caller is responsible for writing them somewhere
the Typst compiler can find them. We use the object-oriented API directly
(`matplotlib.figure.Figure`) rather than `pyplot` to avoid global state and the
non-headless default backend that ships on macOS.

SVG output keeps charts fully vectorial in the final PDF. `svg.fonttype = 'path'`
converts all text to outlines so the SVG is self-contained regardless of which
fonts are installed on the Typst compile host.
"""

from io import BytesIO

import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

GRID_COLOR = '#cccccc'
SPINE_COLOR = '#999999'
TEXT_COLOR = '#1a1a1a'
MUTED_TEXT_COLOR = '#666666'

# Font families requested for chart labels. Matplotlib resolves through this list and falls back
# to its bundled DejaVu Sans if none are installed (e.g. on minimal server images).
SANS_FONT_STACK = ['Public Sans', 'Berkeley Mono']

# Per-category scatter marker styles. B&W printable: filled black circle / gray triangle /
# hollow square are distinguishable by both shape and tone after greyscale conversion.
FOOD_MARKER_STYLES = {
	'Groceries': {'marker': 'o', 'color': '#1a1a1a', 'edgecolors': '#1a1a1a'},
	'Eat Out': {'marker': '^', 'color': '#777777', 'edgecolors': '#777777'},
	'Delivery': {'marker': 's', 'color': 'white', 'edgecolors': '#1a1a1a'},
}


def food_scatter_svg(transactions, target_year, target_month, *, width_in=6.6, height_in=3.5) -> bytes:
	"""Scatter chart of individual food-category transactions over the 12 months preceding target_month.

	X axis = date, Y axis = amount in euros. Each category gets a distinct marker shape.
	A vertical dashed line marks the first day of target_month.
	Returns SVG bytes (vector; no rasterisation).
	"""
	from datetime import date

	if not transactions:
		return _empty_chart_svg(width_in=width_in)

	target_start = date(target_year, target_month, 1)

	with mpl.rc_context(
		{'font.family': 'sans-serif', 'font.sans-serif': SANS_FONT_STACK, 'svg.fonttype': 'path'}
	):
		fig = Figure(figsize=(width_in, height_in))
		ax = fig.subplots()

		for cat_name, style in FOOD_MARKER_STYLES.items():
			cat_txns = [t for t in transactions if t.category == cat_name]
			if not cat_txns:
				continue
			ax.scatter(
				[t.date for t in cat_txns],
				[t.amount for t in cat_txns],
				marker=style['marker'],
				color=style['color'],
				edgecolors=style['edgecolors'],
				linewidths=0.8,
				s=38,
				alpha=0.9,
				label=cat_name,
				zorder=3,
			)

		# Vertical dashed line marking the start of the target month.
		ax.axvline(target_start, linestyle='--', color='#444444', linewidth=0.9, zorder=2)
		# Label the line using a blend transform (x=data coords, y=axes coords) so it
		# stays anchored at the top regardless of the y-axis range.
		ax.text(
			mdates.date2num(target_start),
			0.97,
			f'  {target_start.strftime("%b %Y")}',
			va='top',
			ha='left',
			fontsize=7,
			color='#444444',
			transform=ax.get_xaxis_transform(),
		)

		# X axis: 6 months before the target month through the end of the target month.
		_m = target_month - 6
		window_start = date(target_year - 1, _m + 12, 1) if _m <= 0 else date(target_year, _m, 1)
		_nm = target_month + 1
		window_end = date(target_year + 1, 1, 1) if _nm > 12 else date(target_year, _nm, 1)
		ax.set_xlim(window_start, window_end)
		ax.xaxis.set_major_locator(mdates.MonthLocator())
		ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
		fig.autofmt_xdate(rotation=45, ha='right')
		ax.tick_params(axis='x', colors=MUTED_TEXT_COLOR, labelsize=7)

		# Y axis
		ax.set_ylim(bottom=0)
		ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0f} €'))
		ax.tick_params(axis='y', colors=MUTED_TEXT_COLOR, length=0, labelsize=8)

		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)
		ax.spines['left'].set_color(SPINE_COLOR)
		ax.spines['bottom'].set_color(SPINE_COLOR)

		ax.grid(axis='y', linestyle='-', color=GRID_COLOR, linewidth=0.5)
		ax.set_axisbelow(True)

		ax.legend(fontsize=8, frameon=False, loc='upper left')

		fig.tight_layout(pad=0.4)
		buf = BytesIO()
		fig.savefig(buf, format='svg', bbox_inches='tight')
		return buf.getvalue()


def _empty_chart_svg(*, width_in) -> bytes:
	with mpl.rc_context({'svg.fonttype': 'path'}):
		fig = Figure(figsize=(width_in, 1.2))
		ax = fig.subplots()
		ax.text(
			0.5, 0.5, 'No data', ha='center', va='center', fontsize=10, color=MUTED_TEXT_COLOR, transform=ax.transAxes
		)
		ax.set_axis_off()
		buf = BytesIO()
		fig.savefig(buf, format='svg', bbox_inches='tight')
		return buf.getvalue()
