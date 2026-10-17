from django.db import migrations, models
from django.db.models.functions import Coalesce


class Migration(migrations.Migration):
	dependencies = [
		('core', '0035_retrofill_banktransaction_source_dates'),
	]

	operations = [
		migrations.RemoveConstraint(
			model_name='banktransaction',
			name='bank-transaction-uniqueness-description-date-amount',
		),
		migrations.RemoveField(
			model_name='banktransaction',
			name='date',
		),
		migrations.AddField(
			model_name='banktransaction',
			name='date',
			field=models.GeneratedField(
				db_persist=True,
				expression=Coalesce('transaction_date', 'booking_date', 'value_date'),
				output_field=models.DateField(),
			),
		),
		migrations.AddConstraint(
			model_name='banktransaction',
			constraint=models.UniqueConstraint(
				models.F('description'),
				models.F('date'),
				models.F('amount'),
				name='bank-transaction-uniqueness-description-date-amount',
			),
		),
		migrations.AddConstraint(
			model_name='banktransaction',
			constraint=models.CheckConstraint(
				condition=models.Q(transaction_date__isnull=False)
				| models.Q(booking_date__isnull=False)
				| models.Q(value_date__isnull=False),
				name='bank-transaction-has-a-date',
			),
		),
	]
