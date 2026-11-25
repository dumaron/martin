from django.db import migrations
from django.db.models import F

from core.models.bank_transaction import BankTransaction as CurrentBankTransaction

FINECO_FILE_TYPE = 'FINECO_BANK_ACCOUNT_XLSX_EXPORT'


def fill_transaction_date_from_description(apps, schema_editor):
	BankTransaction = apps.get_model('core', 'BankTransaction')

	BankTransaction.objects.filter(file_import__file_type=FINECO_FILE_TYPE).update(
		booking_date=F('transaction_date'), transaction_date=None
	)

	bank_transactions = list(
		BankTransaction.objects.filter(booking_date__isnull=False)
		.order_by('id')
		.values_list('id', 'description', 'booking_date', 'amount')
	)

	for bank_transaction_id, description, booking_date, amount in bank_transactions:
		transaction_date = CurrentBankTransaction.find_transaction_date_in_description(description, booking_date)
		if transaction_date is None:
			continue

		is_date_already_taken = (
			BankTransaction.objects.filter(description=description, date=transaction_date, amount=amount)
			.exclude(id=bank_transaction_id)
			.exists()
		)
		if is_date_already_taken:
			continue

		BankTransaction.objects.filter(id=bank_transaction_id).update(transaction_date=transaction_date)


def restore_export_dates(apps, schema_editor):
	BankTransaction = apps.get_model('core', 'BankTransaction')

	BankTransaction.objects.exclude(file_import__file_type=FINECO_FILE_TYPE).update(transaction_date=None)
	BankTransaction.objects.filter(file_import__file_type=FINECO_FILE_TYPE).update(
		transaction_date=F('booking_date'), booking_date=None
	)


class Migration(migrations.Migration):
	dependencies = [
		('core', '0037_flashcard_generators'),
	]

	operations = [
		migrations.RunPython(fill_transaction_date_from_description, restore_export_dates),
	]
