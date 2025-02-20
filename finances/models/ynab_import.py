from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

class YnabImport(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   execution_datetime = models.DateTimeField()
   server_knowledge = models.IntegerField(blank=True, null=True)

   def __str__(self):
      return f'YNAB import of {datetime.strftime(self.execution_datetime, "%d/%m/%Y %H:%M %Z")}'