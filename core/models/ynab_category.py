from django.db import models

from core.models.ynab_budget import YnabBudget


class YnabCategory(models.Model):
   id = models.UUIDField(primary_key=True)
   name = models.CharField(max_length=256)
   hidden = models.BooleanField()
   category_group_name = models.CharField(max_length=1024)
   budget = models.ForeignKey(YnabBudget, on_delete=models.CASCADE)

   def __str__(self):
      return self.name

   class Meta:
      db_table = 'ynab_categories'
      verbose_name_plural = 'ynab categories'
