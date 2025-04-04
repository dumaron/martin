from django.db import models
from datetime import datetime

class YnabImport(models.Model):
   execution_datetime = models.DateTimeField()
   server_knowledge = models.IntegerField(blank=True, null=True)

   def __str__(self):
      return f'YNAB import of {datetime.strftime(self.execution_datetime, "%d/%m/%Y %H:%M %Z")}'

   class Meta:
      db_table = 'ynab_imports'
