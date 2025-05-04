from django.db import models


class BankAccount(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=256)
	iban = models.CharField(max_length=34)
	personal = models.BooleanField()

	class Meta:
		db_table = 'bank_accounts'

	def __str__(self):
		return self.name