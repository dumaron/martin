from django.db import migrations, models
from django.db.models import F
from django.db.models.functions import Coalesce

TRANSACTION_DATE_FILE_TYPES = ['FINECO_BANK_ACCOUNT_XLSX_EXPORT']
BOOKING_DATE_FILE_TYPES = [
	'CREDEM_CSV_EXPORT',
	'UNICREDIT_BANK_ACCOUNT_CSV_EXPORT',
	'UNICREDIT_DEBIT_CARD_CSV_EXPORT',
]


def split_date(apps, schema_editor):
	BankTransaction = apps.get_model('core', 'BankTransaction')
	BankTransaction.objects.filter(file_import__file_type__in=TRANSACTION_DATE_FILE_TYPES).update(
		transaction_date=F('date')
	)
	BankTransaction.objects.filter(file_import__file_type__in=BOOKING_DATE_FILE_TYPES).update(booking_date=F('date'))


def merge_dates(apps, schema_editor):
	BankTransaction = apps.get_model('core', 'BankTransaction')
	BankTransaction.objects.update(date=Coalesce('transaction_date', 'booking_date', 'value_date'))


class Migration(migrations.Migration):
	dependencies = [
		('core', '0034_banktransaction_source_dates'),
	]

	operations = [
		migrations.AlterField(
			model_name='banktransaction',
			name='date',
			field=models.DateField(null=True),
		),
		migrations.RunPython(split_date, merge_dates),
	]
