from datetime import date

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
		verbose_name = 'Project'
		verbose_name_plural = 'Projects'


class Todo(models.Model):
	class Statuses(models.TextChoices):
		TODO = 'todo'
		ACTIVE = 'active'
		DONE = 'done'
		ARCHIVED = 'archived'
		DELETED = 'deleted'

	id = models.AutoField(primary_key=True)
	description = models.CharField(max_length=2048)
	project = models.ForeignKey('Project', on_delete=models.CASCADE, blank=True, null=True)
	status = models.CharField(choices=Statuses, max_length=32)
	valid_from = models.DateTimeField(null=True, blank=True)
	deadline = models.DateTimeField(null=True, blank=True)
	priority = models.SmallIntegerField(default=0)
	daily_priority_increase = models.SmallIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	is_valid_order_pray = models.BooleanField(default=False)
	inbox_after_completion = models.TextField(null=True, blank=True)
	waiting_after_completion = models.TextField(null=True, blank=True)
	last_increase = models.DateField(default=date.today)
	snoozed_until = models.DateTimeField(null=True, blank=True)

	def save(self, *args, **kwargs):
		# If the Todo status is "Done" then there is a chance this update is to mark it done from a previous state.
		# We need to check that in order to tell if we need to run the post-completion routines
		if self.status == Todo.Statuses.DONE:
			current_todo = Todo.objects.get(pk=self.id)

			if current_todo.status == Todo.Statuses.TODO or current_todo.status == Todo.Statuses.ACTIVE:
				# Now we're sure we're handling a task that has been marked as completed just now. We can run the
				# post-completion routines.

				# Spawning new Inbox object if specified
				if self.inbox_after_completion != '':
					inbox = Inbox(content=self.inbox_after_completion)
					inbox.save()

				# Spawning new Waiting object if specified
				if self.waiting_after_completion != '':
					waiting = Waiting(content=self.waiting_after_completion, project=self.project)
					waiting.save()

		return super().save(*args, **kwargs)

	def __str__(self):
		return self.description


class Inbox(models.Model):
	class Contexts(models.TextChoices):
		PRIVATE = 'private'
		WORK = 'work'

	class Meta:
		verbose_name_plural = 'inboxes'

	id = models.AutoField(primary_key=True)
	content = models.TextField()
	context = models.TextField(choices=Contexts, default=Contexts.PRIVATE)
	created_at = models.DateTimeField(auto_now_add=True)
	processed_at = models.DateTimeField(null=True, blank=True)
	# But, does it really make sense to have a "deleted" inbox? What is the difference between a deleted box and
	# a processed one with no consequences?
	# I strongly suspect this attribute will be deleted, but let's see after some actual usage.
	deleted_at = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return self.content


class Update(models.Model):
	id = models.AutoField(primary_key=True)
	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'Update for project {self.project} on {self.created_at}'


class Waiting(models.Model):
	class Statuses(models.TextChoices):
		WAITING = 'waiting'
		DONE = 'done'
		DELETED = 'deleted'

	id = models.AutoField(primary_key=True)
	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	content = models.TextField()
	status = models.CharField(max_length=16, choices=Statuses, default=Statuses.WAITING)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.content
