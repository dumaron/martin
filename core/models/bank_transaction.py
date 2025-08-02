import re
from datetime import datetime

from django.db import connection, models


def fix_italian_floating_point(string):
	return string.replace('.', '').replace(',', '.')


# I'm not happy about this approach, but it is a good compromise between creating a "proper" DB structure, which is
# overkill and unnecessarily complex for my needs, and hard-coding too much stuff. Here I inserted into code the IDs of
# the three bank accounts I have on the database. Given that I use a clone of production DB for local development, and
# that I don't change bank accounts often, I can rely on these values being stable enough.
# I hope to discover a more elegant solution with time.
UNICREDIT_BANK_ACCOUNT_ID = 1
FINECO_BANK_ACCOUNT_ID = 2
CREDEM_BANK_ACCOUNT_ID = 3

COMMON_WORDS = ['parma', 'credito', 'pagamento', 'debint', 'debito', 'internazionale']


class BankTransaction(models.Model):
	id = models.AutoField(primary_key=True)
	file_import = models.ForeignKey('BankFileImport', on_delete=models.CASCADE)
	name = models.CharField(max_length=1024)
	date = models.DateField()
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	matched_ynab_transaction = models.ForeignKey(
		'YnabTransaction', null=True, blank=True, on_delete=models.CASCADE
	)
	paired_on = models.DateTimeField(null=True, blank=True)
	snoozed_on = models.DateTimeField(null=True, blank=True)

	# We consider "duplicate" bank transactions the ones that are the same transaction in the real world, but have a
	# slightly different description in the original bank exports. This is often caused by banks changing transaction
	# description from one import to another.
	# I want to link the two (or more??) transactions together, as it can be useful in the future to list all the
	# possible variations in the future.
	duplicate_of = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

	# The bank account this expense is coming from.
	bank_account = models.ForeignKey('BankAccount', on_delete=models.PROTECT)

	class Meta:
		constraints = (
			models.UniqueConstraint('name', 'date', 'amount', name='expense-uniqueness-name-date-amount'),
		)
		db_table = 'bank_transactions'

	@staticmethod
	def from_unicredit_bank_account_csv_row(row, file_import):
		return BankTransaction(
			name=row['Descrizione'].strip(),
			amount=fix_italian_floating_point(row['Importo (EUR)']),
			date=datetime.strptime(row['Data Registrazione'], '%d.%m.%Y'),
			file_import=file_import,
			bank_account_id=UNICREDIT_BANK_ACCOUNT_ID,
		)

	@staticmethod
	def from_unicredit_debit_card_csv_row(row, file_import):
		return BankTransaction(
			name=row['Descrizione'].strip(),
			amount=fix_italian_floating_point(row['Importo']),
			date=datetime.strptime(row['Data Registrazione'], '%d/%m/%Y'),
			file_import=file_import,
			bank_account_id=UNICREDIT_BANK_ACCOUNT_ID,
		)

	@staticmethod
	def from_fineco_bank_account_xslx_row(row, file_import):
		return BankTransaction(
			name=row['Descrizione_Completa'].strip(),
			amount=float(row['Entrate'] or 0) + float(row['Uscite'] or 0),
			date=row['Data_Operazione'],
			file_import=file_import,
			bank_account_id=FINECO_BANK_ACCOUNT_ID,
		)

	@staticmethod
	def from_credem_csv_row(row, file_import):
		return BankTransaction(
			name=row['Descrizione:'],
			amount=float(fix_italian_floating_point(row['Importo']) or 0),
			date=datetime.strptime(row['Data contabile'], '%d/%m/%Y'),
			file_import=file_import,
			bank_account_id=CREDEM_BANK_ACCOUNT_ID,
		)

	def get_potential_duplicate(self) -> 'BankTransaction' or None:
		"""
		Find potential duplicate bank transactions with the same amount and date.
		Bank exports are unreliable: many times they change description text for the same transaction between two exports,
		making matching unreliable.
		"""
		return BankTransaction.objects.filter(amount=self.amount, date=self.date).exclude(id=self.id).first()

	def get_similar_transactions(self, amount=10):
		"""
		Get the bank transactions with the most similar description to this one.
		"""
		# Extract meaningful terms
		words = re.findall(r'\b[a-zA-Z]{3,}\b', self.name.lower())
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
				[fts_query, self.id],
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

	def __str__(self):
		return self.name
