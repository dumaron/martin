from io import BytesIO

import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from apps.website.utils.charts import GRID_COLOR, MUTED_TEXT_COLOR, SANS_FONT_STACK, SPINE_COLOR
from datetime import date


# Font families requested for chart labels. Matplotlib resolves through this list and falls back
# to its bundled DejaVu Sans if none are installed (e.g. on minimal server images).

# Per-category scatter marker styles. B&W printable: filled black circle / gray triangle /
# hollow square are distinguishable by both shape and tone after greyscale conversion.
# Display label → matcher + style. `match` is compared against the YNAB category name on the
# transaction; the dict key is what appears in the chart legend.
FOOD_MARKER_STYLES = {
	'Groceries': {'match': 'Grocery', 'marker': 'o', 'color': '#1a1a1a', 'edgecolors': '#1a1a1a'},
	'Eat Out': {'match': 'Eat out', 'marker': '^', 'color': '#777777', 'edgecolors': '#777777'},
	'Delivery': {'match': 'Delivery', 'marker': 's', 'color': 'white', 'edgecolors': '#1a1a1a'},
}


def food_scatter_svg(transactions, target_year, target_month) -> bytes:
	"""Scatter chart of individual food-category transactions over the 12 months preceding target_month.

	X axis = date, Y axis = amount in euros. Each category gets a distinct marker shape.
	A vertical dashed line marks the first day of target_month.
	Returns SVG bytes (vector; no rasterisation).
	"""

	target_start = date(target_year, target_month, 1)

	with mpl.rc_context(
		{'font.family': 'sans-serif', 'font.sans-serif': SANS_FONT_STACK, 'svg.fonttype': 'path'}
	):
		fig = Figure(figsize=(7.6, 3.5))
		ax = fig.subplots()

		for display_label, style in FOOD_MARKER_STYLES.items():
			cat_txns = list(filter(lambda t: t.matched_ynab_transaction.category.name == style['match'], transactions))
			if not cat_txns:
				continue
			ax.scatter(
				list(map(lambda t: t.date, cat_txns)),
				list(map(lambda t: abs(t.amount), cat_txns)),
				marker=style['marker'],
				color=style['color'],
				edgecolors=style['edgecolors'],
				linewidths=0.8,
				s=38,
				alpha=0.9,
				label=display_label,
				zorder=3,
				clip_on=False,
			)

		# X axis: 6 months before the target month through the end of the target month.
		_m = target_month - 6
		window_start = date(target_year - 1, _m + 12, 1) if _m <= 0 else date(target_year, _m, 1)
		_nm = target_month + 1
		window_end = date(target_year + 1, 1, 1) if _nm > 12 else date(target_year, _nm, 1)
		ax.set_xlim(window_start, window_end)

		# Enumerate the first of each month from window_start up to (and including) window_end.
		# The last entry is the right boundary used to compute the final section's midpoint.
		month_starts = []
		y, m = window_start.year, window_start.month
		while date(y, m, 1) < window_end:
			month_starts.append(date(y, m, 1))
			y, m = (y + 1, 1) if m == 12 else (y, m + 1)
		month_starts.append(window_end)

		# Highlight the target month with a slightly darker background band. zorder=0 keeps
		# the band below the y-axis grid (set_axisbelow puts the grid around zorder 0.5), so
		# horizontal gridlines remain visible through the highlight.
		ax.axvspan(target_start, window_end, facecolor='#ececec', edgecolor='none', zorder=0)

		# Vertical separator at each month boundary.
		for ms in month_starts:
			ax.axvline(ms, linestyle='-', color=GRID_COLOR, linewidth=0.5, zorder=1.5)

		# Horizontal month label centred between each pair of consecutive boundaries.
		for ms, next_ms in zip(month_starts[:-1], month_starts[1:]):
			midpoint = mdates.date2num(ms) + (mdates.date2num(next_ms) - mdates.date2num(ms)) / 2
			ax.text(
				midpoint,
				1.0,
				ms.strftime('%b %y'),
				va='bottom',
				ha='center',
				fontsize=7,
				color=MUTED_TEXT_COLOR,
				transform=ax.get_xaxis_transform(),
			)

		# Inline month labels replace the bottom tick labels; suppress the default ones.
		ax.tick_params(axis='x', which='both', bottom=False, labelbottom=False)

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

		ax.legend(
			fontsize=8,
			frameon=False,
			loc='upper center',
			bbox_to_anchor=(0.5, -0.02),
			ncol=len(FOOD_MARKER_STYLES),
		)

		fig.tight_layout(pad=0.4)
		buf = BytesIO()
		fig.savefig(buf, format='svg', bbox_inches='tight')
		return buf.getvalue()
