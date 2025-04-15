from django.db import models

class YnabBudget(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ynab_budgets'