from django.db import models

class YnabCategory(models.Model):
   id = models.UUIDField(primary_key=True)
   name = models.CharField(max_length=256)
   hidden = models.BooleanField()
   category_group_name = models.CharField(max_length=1024)

   def __str__(self):
      return self.name

   class Meta:
      db_table = 'ynab_categories'
