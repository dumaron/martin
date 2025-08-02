import re

from django.db import connection

from core.models import BankTransaction


def get_similar_bank_transactions(phrase, bank_transaction_id, amount=10):
	"""
	Still TODO
	"""
	# Extract meaningful terms
	words = re.findall(r'\b[a-zA-Z]{3,}\b', phrase.lower())
	meaningful_words = words[-5:]

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
	ORDER BY relevance_score
	LIMIT %s
""",
			[fts_query, amount],
		)

		rows = cursor.fetchall()

		# Extract bank transaction IDs from rows
		transaction_ids = [row[0] for row in rows]

		# Get corresponding BankTransaction objects
		results = BankTransaction.objects.filter(id__in=transaction_ids)

		return results
