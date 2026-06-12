from django.db import models


class Transaction(models.Model):
	# Groups facts and retractions "learned together" and carries their lifecycle: a transaction is built
	# (`created_at`) and later applied/committed (`applied_at`). A null `applied_at` means the transaction
	# is still a draft; reads of "current" knowledge should filter on `applied_at IS NOT NULL`.

	created_at = models.DateTimeField(auto_now_add=True)
	applied_at = models.DateTimeField(blank=True, null=True)
	description = models.TextField(blank=True, null=True)

	class Meta:
		db_table = 'hkm_transactions'

	def __str__(self):
		return f'Transaction {self.id} ({self.description or "no description"})'
