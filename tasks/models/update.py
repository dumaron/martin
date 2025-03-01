from django.db import models
from .project import Project


class Update(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'updates'

    def __str__(self):
        return f'Update for project {self.project} on {self.created_at}'
