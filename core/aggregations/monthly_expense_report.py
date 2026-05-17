# from collections import defaultdict
# from dataclasses import dataclass, field
# from datetime import date
#
# from core.models import BankTransaction, YnabCategory
# from core.utils.datetime import months_back
#
# UNCATEGORIZED_KEY = '__uncategorized__'
# HISTORY_MONTHS = 6
#
#
# MonthlyTotal = tuple[int, int, float]  # (year, month, total)
#
#
# @dataclass
# class CategoryBreakdown:
# 	name: str
# 	group_name: str
# 	month_total: float
# 	monthly_history: list[MonthlyTotal]
# 	same_month_last_year_total: float
#
#
# @dataclass
# class TransactionRow:
# 	date: date
# 	description: str
# 	amount: float
# 	category_name: str
#
#
# @dataclass
# class FoodTransactionRow:
# 	date: date
# 	amount: float
# 	category: str  # canonical: 'Groceries', 'Eat Out', or 'Delivery'
#
#
# @dataclass
# class MonthlyReport:
# 	year: int
# 	month: int
# 	month_total: float
# 	monthly_history: list[MonthlyTotal]
# 	same_month_last_year_total: float
# 	categories: list[CategoryBreakdown]
# 	transactions: list[TransactionRow]
# 	food_transactions: list[FoodTransactionRow] = field(default_factory=list)
#
#
# def _next_month(year, month):
# 	return (year + 1, 1) if month == 12 else (year, month + 1)
#
#
# # def _food_category_name_map() -> dict:
# # 	"""Return {ynab_category_id: canonical_display_name} for all food-related categories."""
# # 	q = Q(name__icontains='grocer') | Q(name__icontains='eat') | Q(name__icontains='delivery')
# # 	result = {}
# # 	for cat in YnabCategory.objects.filter(q):
# # 		name_lower = cat.name.lower()
# # 		for pattern, canonical in FOOD_PATTERNS:
# # 			if pattern in name_lower:
# # 				result[cat.id] = canonical
# # 				break
# # 	return result
#
#
# def build_monthly_expense_report(year, month) -> MonthlyReport:
# 	"""
# 	Aggregate paired bank-transaction expenses on the shared bank account for a given month
# 	and the comparison windows used by the report (previous 5 months + same month last year).
#
# 	Only bank transactions on a shared account, paired to a non-transfer YNAB transaction
# 	with a negative amount, are considered expenses. Bank transaction amount is the source
# 	of truth; the matched YNAB transaction is used solely to read the category.
# 	"""
# 	history = months_back(year, month, HISTORY_MONTHS)
# 	last_year_key = (year - 1, month)
#
# 	# Earliest bucket we need is the year-ago month (older than the 5-month history window).
# 	start = date(last_year_key[0], last_year_key[1], 1)
# 	end_year, end_month = _next_month(year, month)
# 	end = date(end_year, end_month, 1)
#
# 	expenses = list(
# 		BankTransaction.objects.filter(
# 			bank_account__personal=False,
# 			matched_ynab_transaction__isnull=False,
# 			matched_ynab_transaction__transfer_account_id__isnull=True,
# 			amount__lt=0,
# 			date__gte=start,
# 			date__lt=end,
# 		).select_related('matched_ynab_transaction')
# 	)
#
# 	# Bucket totals by (year, month)
# 	overall_by_ym = defaultdict(float)
# 	per_category_by_ym = defaultdict(lambda: defaultdict(float))
#
# 	for t in expenses:
# 		ym = (t.date.year, t.date.month)
# 		amount = float(abs(t.amount))
# 		overall_by_ym[ym] += amount
# 		cat_id = t.matched_ynab_transaction.category_id or UNCATEGORIZED_KEY
# 		per_category_by_ym[cat_id][ym] += amount
#
# 	category_ids = [k for k in per_category_by_ym if k != UNCATEGORIZED_KEY]
# 	categories_by_id = {c.id: c for c in YnabCategory.objects.filter(id__in=category_ids)}
#
# 	def category_label(cat_id):
# 		if cat_id == UNCATEGORIZED_KEY:
# 			return ('Uncategorized', '')
# 		cat = categories_by_id.get(cat_id)
# 		if cat is None:
# 			return (str(cat_id), '')
# 		return (cat.name, cat.category_group_name)
#
# 	category_breakdowns = []
# 	for cat_id, monthly in per_category_by_ym.items():
# 		name, group = category_label(cat_id)
# 		category_breakdowns.append(
# 			CategoryBreakdown(
# 				name=name,
# 				group_name=group,
# 				month_total=monthly.get((year, month), 0.0),
# 				monthly_history=[(y, m, monthly.get((y, m), 0.0)) for y, m in history],
# 				same_month_last_year_total=monthly.get(last_year_key, 0.0),
# 			)
# 		)
# 	category_breakdowns.sort(key=lambda c: c.month_total, reverse=True)
# 	# Drop categories that had no spending this month (kept only if they were active in past months)
# 	category_breakdowns = [c for c in category_breakdowns if c.month_total > 0]
#
# 	transactions = []
# 	for t in expenses:
# 		if t.date.year != year or t.date.month != month:
# 			continue
# 		ynab = t.matched_ynab_transaction
# 		cat_id = ynab.category_id or UNCATEGORIZED_KEY
# 		# YNAB memo is the curated description; fall back to the raw bank name when the memo is empty
# 		# so rows are never blank.
# 		description = (ynab.memo or '').strip() or t.name
# 		transactions.append(
# 			TransactionRow(
# 				date=t.date, description=description, amount=float(abs(t.amount)), category_name=category_label(cat_id)[0]
# 			)
# 		)
# 	transactions.sort(key=lambda r: (r.date, r.amount), reverse=True)
#
# 	# Food-category scatter data: 6 months before the target month plus the target month itself.
# 	# `end` (start of the month after target) is already computed above and used as the query bound.
# 	food_cats = _food_category_name_map()
# 	_m = month - 6
# 	food_window_start = date(year - 1, _m + 12, 1) if _m <= 0 else date(year, _m, 1)
# 	food_transactions = sorted(
# 		[
# 			FoodTransactionRow(
# 				date=t.date, amount=float(abs(t.amount)), category=food_cats[t.matched_ynab_transaction.category_id]
# 			)
# 			for t in expenses
# 			if t.matched_ynab_transaction.category_id in food_cats and t.date >= food_window_start
# 		],
# 		key=lambda r: r.date,
# 	)
#
# 	return MonthlyReport(
# 		year=year,
# 		month=month,
# 		month_total=overall_by_ym.get((year, month), 0.0),
# 		monthly_history=[(y, m, overall_by_ym.get((y, m), 0.0)) for y, m in history],
# 		same_month_last_year_total=overall_by_ym.get(last_year_key, 0.0),
# 		categories=category_breakdowns,
# 		transactions=transactions,
# 		food_transactions=food_transactions,
# 	)
#
#
