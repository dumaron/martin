from django.db import transaction as db_transaction
from django.utils import timezone

from core.hkm.models import Fact, Transaction


def create_draft(facts, description=''):
	# Stage a batch of (subject, predicate, object) triples as a *draft*: the transaction is created without
	# an `applied_at`, so the facts are not yet part of current knowledge. Apply it later to commit them.
	with db_transaction.atomic():
		draft = Transaction.objects.create(description=description or None)
		Fact.objects.bulk_create(
			Fact(subject=subject, predicate=predicate, object=value, transaction=draft)
			for subject, predicate, value in facts
		)
	return draft


def apply_transaction(transaction):
	# Commit a draft by stamping `applied_at`; from then on its facts count as current. Re-applying is a no-op.
	if transaction.applied_at is None:
		transaction.applied_at = timezone.now()
		transaction.save(update_fields=['applied_at'])
	return transaction


def discard_draft(transaction):
	# Throw away an unapplied draft and the facts it staged. Applied transactions are immutable history and
	# must not be discarded — correct them by retracting individual facts instead.
	if transaction.applied_at is not None:
		raise ValueError('Cannot discard a transaction that has already been applied.')
	with db_transaction.atomic():
		transaction.facts.all().delete()
		transaction.delete()
