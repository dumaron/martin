import re

from django.db import connection

from core.models import BankTransaction

COMMON_WORDS = ['parma', 'credito', 'pagamento', 'debint', 'debito', 'internazionale']


def get_similar_bank_transactions(phrase, bank_transaction_id, amount=10):
	"""
	Get the bank transactions with the most similar description of the one of the given bank transaction.
	"""

	# Extract meaningful terms
	words = re.findall(r'\b[a-zA-Z]{3,}\b', phrase.lower())
	meaningful_words = [word for word in words if word not in COMMON_WORDS][-5:]

	if not meaningful_words:
		return BankTransaction.objects.none()

	# Build FTS5 query
	fts_query = ' OR '.join([f'"{word}"' for word in meaningful_words])

	with connection.cursor() as cursor:
		cursor.execute(
			"""
	SELECT
		 bank_transactions_fts.*,
	    bm25(bank_transactions_fts) as relevance_score
	FROM bank_transactions_fts
	WHERE bank_transactions_fts MATCH %s
	AND bank_transactions_fts.id != %s
	ORDER BY relevance_score DESC
	LIMIT 100 -- Look at the big comment below for an explanation
""",
			[fts_query, bank_transaction_id],
		)

		rows = cursor.fetchall()

		# Extract bank transaction IDs from rows
		transaction_ids = [row[0] for row in rows]

		# Get corresponding BankTransaction objects
		# It would have been also ok to filter for duplicates in the FTS query, if only the field for duplication was available.
		# I didn't want to get that table too "dirty", so I opted instead for over-fetching ids from the virtual table, and then
		# completing the filter here. If this ever leads to errors, I can always add a column to the virtual table and then
		# filter duplicates in the original query.
		results = BankTransaction.objects.filter(id__in=transaction_ids, duplicate_of__isnull=True)[:amount]

		return results
