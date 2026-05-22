from datetime import date
from io import BytesIO
from itertools import groupby

import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from apps.website.utils.charts import GRID_COLOR, MUTED_TEXT_COLOR, SANS_FONT_STACK, SPINE_COLOR
from core.constants import EXTRAORDINARY_YNAB_GROUP_CATEGORY_NAME


def _is_extraordinary(t) -> bool:
	cat = t.matched_ynab_transaction.category
	return cat is not None and cat.category_group_name == EXTRAORDINARY_YNAB_GROUP_CATEGORY_NAME


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

# Series for the monthly-totals line chart. `match=None` means "sum across all food
# categories" (i.e. the overall total, which still includes Delivery even though Delivery
# is not drawn as its own line).
FOOD_TOTAL_LINE_STYLES = {
	'Total': {'match': None, 'linestyle': '--', 'color': '#1a1a1a', 'marker': 'D'},
	'Groceries': {
		'match': FOOD_MARKER_STYLES['Groceries']['match'],
		'linestyle': '-',
		'color': '#1a1a1a',
		'marker': 'o',
	},
	'Eat Out': {
		'match': FOOD_MARKER_STYLES['Eat Out']['match'],
		'linestyle': '-',
		'color': '#777777',
		'marker': '^',
	},
}

# Series for the overall-expenses monthly-totals line chart. `predicate=None` means "every
# expense in the input set" (the Total line). Other entries split the same input by whether
# the transaction sits in the Extraordinary YNAB group or not.
EXPENSES_TOTAL_LINE_STYLES = {
	'Total': {'predicate': None, 'linestyle': '--', 'color': '#1a1a1a', 'marker': 'D'},
	'Other': {
		'predicate': lambda t: not _is_extraordinary(t),
		'linestyle': '-',
		'color': '#1a1a1a',
		'marker': 'o',
	},
	'Extraordinary': {'predicate': _is_extraordinary, 'linestyle': '-', 'color': '#777777', 'marker': '^'},
}

# Categories with a monthly total below this threshold (in €) are lumped into the "Other" bar
# pinned to the bottom of `category_totals_svg`.
CATEGORY_TOTALS_OTHER_THRESHOLD = 50


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
			fontsize=8, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=len(FOOD_MARKER_STYLES)
		)

		fig.tight_layout(pad=0.4)
		buf = BytesIO()
		fig.savefig(buf, format='svg', bbox_inches='tight')
		return buf.getvalue()


def food_totals_svg(transactions, target_year, target_month) -> bytes:
	"""Line chart of monthly food spending totals over the same 7-month window as the scatter.

	One point per month per series: overall food total, Groceries, and Eat Out. Delivery is
	intentionally not drawn as a separate line, but it is still included in the overall total.
	Returns SVG bytes.
	"""

	target_start = date(target_year, target_month, 1)

	with mpl.rc_context(
		{'font.family': 'sans-serif', 'font.sans-serif': SANS_FONT_STACK, 'svg.fonttype': 'path'}
	):
		fig = Figure(figsize=(7.6, 3.5))
		ax = fig.subplots()

		# X axis: 6 months before the target month through the end of the target month.
		_m = target_month - 6
		window_start = date(target_year - 1, _m + 12, 1) if _m <= 0 else date(target_year, _m, 1)
		_nm = target_month + 1
		window_end = date(target_year + 1, 1, 1) if _nm > 12 else date(target_year, _nm, 1)
		ax.set_xlim(window_start, window_end)

		# Enumerate the first of each month in the window (plus window_end as the right boundary).
		month_starts = []
		y, m = window_start.year, window_start.month
		while date(y, m, 1) < window_end:
			month_starts.append(date(y, m, 1))
			y, m = (y + 1, 1) if m == 12 else (y, m + 1)
		month_starts.append(window_end)

		month_pairs = list(zip(month_starts[:-1], month_starts[1:]))

		# Aggregate: sum of |amount| per (month, optional category) bucket.
		def sum_for_month(ms, next_ms, category_name=None):
			in_window = filter(lambda t: ms <= t.date < next_ms, transactions)
			if category_name is not None:
				in_window = filter(lambda t: t.matched_ynab_transaction.category.name == category_name, in_window)
			return sum(map(lambda t: abs(t.amount), in_window))

		x_midpoints = list(
			map(lambda p: mdates.date2num(p[0]) + (mdates.date2num(p[1]) - mdates.date2num(p[0])) / 2, month_pairs)
		)

		# Highlight band (target month) — zorder=0 so the y-grid stays visible on top.
		ax.axvspan(target_start, window_end, facecolor='#ececec', edgecolor='none', zorder=0)

		# Vertical separator at each month boundary.
		for ms in month_starts:
			ax.axvline(ms, linestyle='-', color=GRID_COLOR, linewidth=0.5, zorder=1.5)

		# Horizontal month label centred between each pair of consecutive boundaries.
		for ms, next_ms in month_pairs:
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

		# One line per series.
		for display_label, style in FOOD_TOTAL_LINE_STYLES.items():
			series = list(map(lambda p: sum_for_month(p[0], p[1], style['match']), month_pairs))
			ax.plot(
				x_midpoints,
				series,
				linestyle=style['linestyle'],
				color=style['color'],
				linewidth=1.0,
				marker=style['marker'],
				markersize=5,
				markerfacecolor=style['color'],
				markeredgecolor=style['color'],
				label=display_label,
				zorder=3,
				clip_on=False,
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
			ncol=len(FOOD_TOTAL_LINE_STYLES),
		)

		fig.tight_layout(pad=0.4)
		buf = BytesIO()
		fig.savefig(buf, format='svg', bbox_inches='tight')
		return buf.getvalue()


def category_totals_svg(transactions, target_year, target_month) -> bytes:
	"""Horizontal bar chart of total spend per YNAB category for the target month.

	Bars are sorted descending (largest at the top). Transactions whose matched YNAB
	transaction has no category are bucketed as "Uncategorized".
	Returns SVG bytes.
	"""

	month_txns = list(
		filter(lambda t: t.date.year == target_year and t.date.month == target_month, transactions)
	)

	def category_label(t):
		cat = t.matched_ynab_transaction.category
		return cat.name if cat else 'Uncategorized'

	# Aggregate |amount| per category. `groupby` requires the input to be sorted by the same key.
	sorted_txns = sorted(month_txns, key=category_label)
	totals = {
		label: sum(map(lambda t: float(abs(t.amount)), group))
		for label, group in groupby(sorted_txns, key=category_label)
	}

	# Split: categories at/above the threshold stay individual; the rest collapse into "Other"
	# pinned to the bottom of the chart.
	kept = list(filter(lambda kv: kv[1] >= CATEGORY_TOTALS_OTHER_THRESHOLD, totals.items()))
	rest = list(filter(lambda kv: kv[1] < CATEGORY_TOTALS_OTHER_THRESHOLD, totals.items()))

	# barh draws bottom-up, so order is: [Other (if any), smallest kept, ..., largest kept].
	kept_asc = sorted(kept, key=lambda kv: kv[1])
	other_items = [('Other', sum(map(lambda kv: kv[1], rest)))] if rest else []
	ordered = other_items + kept_asc
	labels = list(map(lambda kv: kv[0], ordered))
	values = list(map(lambda kv: kv[1], ordered))
	bar_colors = list(map(lambda label: '#777777' if label == 'Other' else '#1a1a1a', labels))

	with mpl.rc_context(
		{'font.family': 'sans-serif', 'font.sans-serif': SANS_FONT_STACK, 'svg.fonttype': 'path'}
	):
		# Scale height with the number of bars so labels don't collide.
		fig_height = max(2.5, 0.32 * len(labels) + 0.8)
		fig = Figure(figsize=(7.6, fig_height))
		ax = fig.subplots()

		ax.barh(labels, values, color=bar_colors, height=0.6, zorder=3)

		# Value label at the end of each bar.
		for i, v in enumerate(values):
			ax.text(v, i, f'  {v:.0f} €', va='center', ha='left', fontsize=8, color=MUTED_TEXT_COLOR)

		# Leave headroom on the right so the value labels don't get clipped.
		if values:
			ax.set_xlim(right=max(values) * 1.15)

		ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0f} €'))
		ax.tick_params(axis='x', colors=MUTED_TEXT_COLOR, length=0, labelsize=8)
		ax.tick_params(axis='y', colors=MUTED_TEXT_COLOR, length=0, labelsize=8)

		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)
		ax.spines['left'].set_color(SPINE_COLOR)
		ax.spines['bottom'].set_color(SPINE_COLOR)

		ax.grid(axis='x', linestyle='-', color=GRID_COLOR, linewidth=0.5)
		ax.set_axisbelow(True)

		fig.tight_layout(pad=0.4)
		buf = BytesIO()
		fig.savefig(buf, format='svg', bbox_inches='tight')
		return buf.getvalue()


def expenses_totals_svg(transactions, target_year, target_month) -> bytes:
	"""Line chart of monthly overall expense totals: Total, Other, and Extraordinary.

	Same 7-month window and visual frame as the food charts. Series are split by whether the
	matched YNAB category belongs to the Extraordinary group; the Total line covers all of
	the input set (which is assumed to already be filtered to expenses).
	Returns SVG bytes.
	"""

	target_start = date(target_year, target_month, 1)

	with mpl.rc_context(
		{'font.family': 'sans-serif', 'font.sans-serif': SANS_FONT_STACK, 'svg.fonttype': 'path'}
	):
		fig = Figure(figsize=(7.6, 3.5))
		ax = fig.subplots()

		# X axis: 6 months before the target month through the end of the target month.
		_m = target_month - 6
		window_start = date(target_year - 1, _m + 12, 1) if _m <= 0 else date(target_year, _m, 1)
		_nm = target_month + 1
		window_end = date(target_year + 1, 1, 1) if _nm > 12 else date(target_year, _nm, 1)
		ax.set_xlim(window_start, window_end)

		# Enumerate the first of each month in the window (plus window_end as right boundary).
		month_starts = []
		y, m = window_start.year, window_start.month
		while date(y, m, 1) < window_end:
			month_starts.append(date(y, m, 1))
			y, m = (y + 1, 1) if m == 12 else (y, m + 1)
		month_starts.append(window_end)

		month_pairs = list(zip(month_starts[:-1], month_starts[1:]))

		# Aggregate: sum of |amount| per (month, optional predicate) bucket.
		def sum_for_month(ms, next_ms, predicate=None):
			in_window = filter(lambda t: ms <= t.date < next_ms, transactions)
			if predicate is not None:
				in_window = filter(predicate, in_window)
			return sum(map(lambda t: abs(t.amount), in_window))

		x_midpoints = list(
			map(lambda p: mdates.date2num(p[0]) + (mdates.date2num(p[1]) - mdates.date2num(p[0])) / 2, month_pairs)
		)

		# Highlight band (target month) — zorder=0 so the y-grid stays visible on top.
		ax.axvspan(target_start, window_end, facecolor='#ececec', edgecolor='none', zorder=0)

		# Vertical separator at each month boundary.
		for ms in month_starts:
			ax.axvline(ms, linestyle='-', color=GRID_COLOR, linewidth=0.5, zorder=1.5)

		# Horizontal month label centred between each pair of consecutive boundaries.
		for ms, next_ms in month_pairs:
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

		# One line per series.
		for display_label, style in EXPENSES_TOTAL_LINE_STYLES.items():
			series = list(map(lambda p: sum_for_month(p[0], p[1], style['predicate']), month_pairs))
			ax.plot(
				x_midpoints,
				series,
				linestyle=style['linestyle'],
				color=style['color'],
				linewidth=1.0,
				marker=style['marker'],
				markersize=5,
				markerfacecolor=style['color'],
				markeredgecolor=style['color'],
				label=display_label,
				zorder=3,
				clip_on=False,
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
			ncol=len(EXPENSES_TOTAL_LINE_STYLES),
		)

		fig.tight_layout(pad=0.4)
		buf = BytesIO()
		fig.savefig(buf, format='svg', bbox_inches='tight')
		return buf.getvalue()
