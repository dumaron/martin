from django.db import models


class YnabAccount(models.Model):
	id = models.UUIDField(primary_key=True)
	name = models.CharField(max_length=256)
	budget = models.ForeignKey('YnabBudget', on_delete=models.CASCADE)

	def __str__(self):
		return self.name

	class Meta:
		db_table = 'ynab_accounts'
