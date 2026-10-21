from django.db import migrations, models


class Migration(migrations.Migration):
	dependencies = [
		('core', '0033_banktransactiondescriptionhint_and_more'),
	]

	operations = [
		migrations.AddField(
			model_name='banktransaction',
			name='transaction_date',
			field=models.DateField(blank=True, null=True),
		),
		migrations.AddField(
			model_name='banktransaction',
			name='booking_date',
			field=models.DateField(blank=True, null=True),
		),
		migrations.AddField(
			model_name='banktransaction',
			name='value_date',
			field=models.DateField(blank=True, null=True),
		),
	]
