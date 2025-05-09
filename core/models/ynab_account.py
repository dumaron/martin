from django.db import models


class YnabAccount(models.Model):
	id = models.UUIDField(primary_key=True)
	name = models.CharField(max_length=256)
	budget = models.ForeignKey('YnabBudget', on_delete=models.CASCADE)
	linked_bank_account = models.ForeignKey('BankAccount', on_delete=models.CASCADE, null=True, blank=True)

	def __str__(self):
		return self.name

	class Meta:
		db_table = 'ynab_accounts'
