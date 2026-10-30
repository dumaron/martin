from django.core.exceptions import ValidationError
from django.db import models

from core import hkm
from core.hkm.hkmq import VARIABLE

TEMPLATES = ('question_template', 'answer_template')


def template_variables(template):
	return set(map(lambda variable: variable[1:], VARIABLE.findall(template)))


def fill(template, row):
	return VARIABLE.sub(lambda match: row[match[0][1:]], template)


class FlashcardGenerator(models.Model):
	name = models.CharField(max_length=200)
	query = models.TextField()
	question_template = models.TextField()
	answer_template = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'flashcard_generators'

	def __str__(self):
		return self.name

	def clean(self):
		try:
			variables = set(hkm.query_variables(self.query))
		except hkm.QueryError as error:
			raise ValidationError({'query': str(error)})

		unknown = {field: template_variables(getattr(self, field)) - variables for field in TEMPLATES}
		errors = {
			field: f'Not in the query: ${", $".join(sorted(names))}' for field, names in unknown.items() if names
		}
		if errors:
			raise ValidationError(errors)

	def cards(self):
		used = template_variables(self.question_template) | template_variables(self.answer_template)
		rows = filter(lambda row: None not in map(row.get, used), hkm.run_query(self.query))
		return set(map(lambda row: (fill(self.question_template, row), fill(self.answer_template, row)), rows))
