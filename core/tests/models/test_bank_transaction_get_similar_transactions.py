from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from core.models import BankAccount, BankFileImport, BankTransaction


class BankTransactionGetSimilarTransactionsTest(TestCase):
	"""Test the get_similar_transactions method of BankTransaction model."""

	def setUp(self):
		"""Set up test data."""
		# Create test bank accounts
		self.bank_account = BankAccount.objects.create(
			name='Test Bank Account', iban='IT60X0542811101000000123456', personal=True
		)

		# Create a mock CSV file for testing
		test_csv_content = 'Data;Descrizione;Importo\n2024-01-15;Test transaction;100.50'
		mock_file = SimpleUploadedFile('test_import.csv', test_csv_content.encode('utf-8'), content_type='text/csv')

		# Mock the file processing to avoid actual file operations during testing
		with patch.object(BankFileImport, 'get_file_rows', return_value=[]):
			self.file_import = BankFileImport.objects.create(
				file_name='test_import.csv',
				file_type=BankFileImport.FileType.UNICREDIT_BANK_ACCOUNT_CSV_EXPORT,
				bank_file=mock_file,
			)

		# Create test transactions for similarity testing
		self.transaction1 = BankTransaction.objects.create(
			id=1,
			name='AMAZON MARKETPLACE EU-SARL LUXEMBOURG',
			date=date(2024, 1, 15),
			amount=Decimal('25.99'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		self.transaction2 = BankTransaction.objects.create(
			id=2,
			name='PAYPAL IRELAND LIMITED DUBLIN',
			date=date(2024, 1, 16),
			amount=Decimal('15.50'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		self.transaction3 = BankTransaction.objects.create(
			id=3,
			name='AMAZON PRIME VIDEO UK LONDON',
			date=date(2024, 1, 17),
			amount=Decimal('8.99'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		self.transaction4 = BankTransaction.objects.create(
			id=4,
			name='SPOTIFY AB STOCKHOLM',
			date=date(2024, 1, 18),
			amount=Decimal('9.99'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Transaction marked as duplicate (should be excluded from results)
		self.duplicate_transaction = BankTransaction.objects.create(
			id=5,
			name='AMAZON DUPLICATE TRANSACTION',
			date=date(2024, 1, 19),
			amount=Decimal('12.99'),
			file_import=self.file_import,
			bank_account=self.bank_account,
			duplicate_of=self.transaction1,
		)

	@patch('core.models.bank_transaction.connection')
	def test_returns_empty_queryset_when_no_meaningful_words(self, mock_connection):
		"""Test that method returns empty queryset when no meaningful words are found."""
		transaction = BankTransaction.objects.create(
			name='parma credito debito',  # All common words
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		result = transaction.get_similar_transactions()

		self.assertEqual(list(result), [])
		mock_connection.cursor.assert_not_called()

	@patch('core.models.bank_transaction.connection')
	def test_returns_empty_queryset_when_no_meaningful_words_case_insensitive(self, mock_connection):
		"""Test that method returns empty queryset when no meaningful words are found."""
		transaction = BankTransaction.objects.create(
			name='PARMA DEBITO CREDITO',  # All common words - but uppercase
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		result = transaction.get_similar_transactions()

		self.assertEqual(list(result), [])
		mock_connection.cursor.assert_not_called()

	@patch('core.models.bank_transaction.connection')
	def test_returns_empty_queryset_when_name_is_empty(self, mock_connection):
		"""Test that method returns empty queryset when name is empty."""
		transaction = BankTransaction.objects.create(
			name='',
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		result = transaction.get_similar_transactions()

		self.assertEqual(list(result), [])
		mock_connection.cursor.assert_not_called()

	@patch('core.models.bank_transaction.connection')
	def test_returns_empty_queryset_when_name_contains_only_short_words(self, mock_connection):
		"""Test that method returns empty queryset when name contains only short words."""
		transaction = BankTransaction.objects.create(
			name='ab cd ef',  # All words less than 3 characters
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		result = transaction.get_similar_transactions()

		self.assertEqual(list(result), [])
		mock_connection.cursor.assert_not_called()

	@patch('core.models.bank_transaction.connection')
	def test_extracts_meaningful_words_correctly(self, mock_connection):
		"""Test that method correctly extracts meaningful words from name."""
		transaction = BankTransaction.objects.create(
			name='AMAZON MARKETPLACE EU credito debito test',
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Mock cursor and database response
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = [
			(2, 'PAYPAL IRELAND LIMITED DUBLIN', date(2024, 1, 16), Decimal('15.50'), 0.8),
			(3, 'AMAZON PRIME VIDEO UK LONDON', date(2024, 1, 17), Decimal('8.99'), 0.7),
		]

		transaction.get_similar_transactions()

		# Verify that the SQL query was called with the correct FTS query
		# Expected meaningful words: ['amazon', 'marketplace', 'test'] (last 5, excluding common words)
		expected_fts_query = '"amazon" OR "marketplace" OR "test"'
		mock_cursor.execute.assert_called_once()
		args, _ = mock_cursor.execute.call_args
		self.assertIn(expected_fts_query, args[1])
		self.assertEqual(args[1][1], transaction.id)  # bank_transaction_id

	@patch('core.models.bank_transaction.connection')
	def test_limits_meaningful_words_to_last_five(self, mock_connection):
		"""Test that method limits meaningful words to the last 5."""
		transaction = BankTransaction.objects.create(
			name='alpha beta gamma delta epsilon zeta eta amazon marketplace',
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Mock cursor and database response
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = []

		transaction.get_similar_transactions()

		# All words are meaningful (none are in COMMON_WORDS), so take last 5
		# ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'amazon', 'marketplace'][-5:]
		# Which should be: ['epsilon', 'zeta', 'eta', 'amazon', 'marketplace']
		expected_fts_query = '"epsilon" OR "zeta" OR "eta" OR "amazon" OR "marketplace"'
		mock_cursor.execute.assert_called_once()
		args, _ = mock_cursor.execute.call_args
		self.assertIn(expected_fts_query, args[1])

	@patch('core.models.bank_transaction.connection')
	def test_excludes_requesting_transaction_from_results(self, mock_connection):
		"""Test that method excludes the requesting transaction from results."""
		# Mock cursor and database response
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = [
			(2, 'PAYPAL IRELAND LIMITED DUBLIN', date(2024, 1, 16), Decimal('15.50'), 0.8)
		]

		self.transaction1.get_similar_transactions()

		# Verify that the SQL query excludes the requesting transaction
		mock_cursor.execute.assert_called_once()
		args, _ = mock_cursor.execute.call_args
		self.assertIn('AND bank_transactions_fts.id != %s', args[0])
		self.assertEqual(args[1][1], self.transaction1.id)

	@patch('core.models.bank_transaction.connection')
	def test_excludes_duplicate_transactions_from_results(self, mock_connection):
		"""Test that method excludes transactions marked as duplicates."""
		# Mock cursor and database response including the duplicate transaction
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = [
			(2, 'PAYPAL IRELAND LIMITED DUBLIN', date(2024, 1, 16), Decimal('15.50'), 0.8),
			(5, 'AMAZON DUPLICATE TRANSACTION', date(2024, 1, 19), Decimal('12.99'), 0.7),  # This is a duplicate
		]

		result = self.transaction1.get_similar_transactions()

		# The result should only contain non-duplicate transactions
		result_ids = [t.id for t in result]
		self.assertIn(2, result_ids)  # Non-duplicate transaction should be included
		self.assertNotIn(5, result_ids)  # Duplicate transaction should be excluded

	@patch('core.models.bank_transaction.connection')
	def test_respects_amount_parameter(self, mock_connection):
		"""Test that method respects the amount parameter for limiting results."""
		# Mock cursor and database response with multiple results
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = [
			(2, 'PAYPAL IRELAND LIMITED DUBLIN', date(2024, 1, 16), Decimal('15.50'), 0.8),
			(3, 'AMAZON PRIME VIDEO UK LONDON', date(2024, 1, 17), Decimal('8.99'), 0.7),
			(4, 'SPOTIFY AB STOCKHOLM', date(2024, 1, 18), Decimal('9.99'), 0.6),
		]

		result = self.transaction1.get_similar_transactions(amount=2)

		# Should return only 2 results despite 3 being available
		self.assertEqual(len(result), 2)

	@patch('core.models.bank_transaction.connection')
	def test_handles_case_insensitive_search(self, mock_connection):
		"""Test that method handles case insensitive search correctly."""
		transaction = BankTransaction.objects.create(
			name='AMAZON marketplace EU-sarl',
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Mock cursor and database response
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = []

		transaction.get_similar_transactions()

		# Verify that words are lowercased in the FTS query
		expected_fts_query = '"amazon" OR "marketplace" OR "sarl"'
		mock_cursor.execute.assert_called_once()
		args, _ = mock_cursor.execute.call_args
		self.assertIn(expected_fts_query, args[1])

	@patch('core.models.bank_transaction.connection')
	def test_filters_out_common_words(self, mock_connection):
		"""Test that method filters out common words defined in COMMON_WORDS."""
		transaction = BankTransaction.objects.create(
			name='amazon parma credito pagamento debint debito internazionale marketplace',
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Mock cursor and database response
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = []

		transaction.get_similar_transactions()

		# Should only include meaningful words, excluding common words
		expected_fts_query = '"amazon" OR "marketplace"'
		mock_cursor.execute.assert_called_once()
		args, _ = mock_cursor.execute.call_args
		self.assertIn(expected_fts_query, args[1])

	@patch('core.models.bank_transaction.connection')
	def test_handles_special_characters_in_name(self, mock_connection):
		"""Test that method handles special characters in name correctly."""
		transaction = BankTransaction.objects.create(
			name='amazon-marketplace.eu/payment (test) & more!',
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Mock cursor and database response
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = []

		transaction.get_similar_transactions()

		# Should extract only alphabetic words of 3+ characters
		expected_fts_query = '"amazon" OR "marketplace" OR "payment" OR "test" OR "more"'
		mock_cursor.execute.assert_called_once()
		args, _ = mock_cursor.execute.call_args
		self.assertIn(expected_fts_query, args[1])

	@patch('core.models.bank_transaction.connection')
	def test_returns_correct_queryset_type(self, mock_connection):
		"""Test that method returns a Django QuerySet of BankTransaction objects."""
		# Mock cursor and database response
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = [
			(2, 'PAYPAL IRELAND LIMITED DUBLIN', date(2024, 1, 16), Decimal('15.50'), 0.8)
		]

		result = self.transaction1.get_similar_transactions()

		# Verify it's a QuerySet
		self.assertTrue(hasattr(result, 'model'))
		self.assertEqual(result.model, BankTransaction)

	@patch('core.models.bank_transaction.connection')
	def test_word_extraction_regex(self, mock_connection):
		"""Test that word extraction regex works correctly."""
		transaction = BankTransaction.objects.create(
			name='test123 abc ab ABC test-word test_word test.word test@email.com',
			date=date(2024, 1, 20),
			amount=Decimal('10.00'),
			file_import=self.file_import,
			bank_account=self.bank_account,
		)

		# Mock cursor and database response
		mock_cursor = MagicMock()
		mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
		mock_cursor.fetchall.return_value = []

		transaction.get_similar_transactions()

		# Should only extract alphabetic words of 3+ characters
		# Extracted words: ['abc', 'abc', 'test', 'word', 'test', 'word', 'test', 'email', 'com']
		# Last 5: ['test', 'word', 'test', 'email', 'com']
		mock_cursor.execute.assert_called_once()
		args, _ = mock_cursor.execute.call_args
		fts_query = args[1][0]

		# Should contain alphabetic words of 3+ characters from the last 5
		self.assertIn('test', fts_query)
		self.assertIn('word', fts_query)
		self.assertIn('email', fts_query)
		self.assertIn('com', fts_query)

		# Should not contain numbers or short words
		self.assertNotIn('123', fts_query)
		self.assertNotIn('ab', fts_query)
