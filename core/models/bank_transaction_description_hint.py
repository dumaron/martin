import re

from django.db import models


class BankTransactionDescriptionHint(models.Model):
	id = models.AutoField(primary_key=True)
	regex = models.CharField(max_length=256)
	hint = models.TextField()

	class Meta:
		db_table = 'bank_transaction_description_hints'

	@classmethod
	def create_from_text(cls, text, hint):
		return cls.objects.create(regex=f'(?i){re.escape(text)}', hint=hint)

	def __str__(self):
		return self.regex
