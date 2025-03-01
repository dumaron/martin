from datetime import datetime
from django.db import models
from core.models.todo import Todo


class DailySuggestion(models.Model):
    """
    A list of Todos that are suggested to be done in a day
    """

    class Meta:
        db_table = 'daily_suggestions'

    date = models.DateField(primary_key=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    added_todos = models.ManyToManyField(Todo, related_name='added_todos', through='DailySuggestionAddedTodo')
    picked_todos = models.ManyToManyField(Todo, related_name='picked_todos', through='DailySuggestionPickedTodo')

    def __str__(self):
        return f'Daily Suggestion {datetime.strftime(self.date, "%Y-%m-%d")}'


class DailySuggestionAddedTodo(models.Model):
    """
    A single Todo added to a DailySuggestion
    """

    suggestion = models.ForeignKey(DailySuggestion, on_delete=models.CASCADE)
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE)

    class Meta:
        db_table = 'daily_suggestion_added_todos'
        unique_together = ('suggestion', 'todo')
        ordering = ['id']


class DailySuggestionPickedTodo(models.Model):
    """
    A single Todo item that has been picked for a DailySuggestion, but not added to id
    """

    suggestion = models.ForeignKey(DailySuggestion, on_delete=models.CASCADE)
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE)

    class Meta:
        db_table = 'daily_suggestion_picked_todos'
        unique_together = ('suggestion', 'todo')
        ordering = ['id']