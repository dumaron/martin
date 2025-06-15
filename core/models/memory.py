from django.db import models


class Memory(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    photo = models.FileField(upload_to='memories/')
    description = models.TextField(blank=True)
    location = models.CharField(max_length=256, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'Memory {self.id}'

    class Meta:
        db_table = 'memories'
        verbose_name_plural = 'memories'