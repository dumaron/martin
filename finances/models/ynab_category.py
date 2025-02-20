from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class YnabCategory(models.Model):
   id = models.UUIDField(primary_key=True)
   name = models.CharField(max_length=256)
   hidden = models.BooleanField()
   category_group_name = models.CharField(max_length=1024)
   user = models.ForeignKey(User, on_delete=models.CASCADE)

   def __str__(self):
      return self.name