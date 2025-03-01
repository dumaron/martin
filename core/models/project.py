from django.db import models
from treenode.models import TreeNodeModel


class Project(TreeNodeModel):
    class Statuses(models.TextChoices):
        ACTIVE = 'active'
        ARCHIVED = 'archived'
        DELETED = 'deleted'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=1024)
    status = models.CharField(choices=Statuses, max_length=32)

    def __str__(self):
        return self.name

    treenode_display_field = 'name'

    class Meta(TreeNodeModel.Meta):
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'