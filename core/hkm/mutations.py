from django.db import transaction as db_transaction
from django.utils import timezone

from core.hkm.models import Fact, Retraction, Transaction


def create_draft(facts, retractions=(), description=''):
	# Stage a batch as a *draft*: new (subject, predicate, object) triples to assert plus the ids of existing
	# facts to retract, all grouped under one unapplied transaction. Nothing affects current knowledge until
	# the transaction is applied — then the new facts appear and the retracted ones disappear together.
	with db_transaction.atomic():
		draft = Transaction.objects.create(description=description or None)
		Fact.objects.bulk_create(
			Fact(subject=subject, predicate=predicate, object=value, transaction=draft)
			for subject, predicate, value in facts
		)
		Retraction.objects.bulk_create(Retraction(fact_id=fact_id, transaction=draft) for fact_id in retractions)
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
		# Retractions first: a fact protected by a retraction can't be deleted, and the staged retractions
		# point at facts we want to leave current.
		transaction.retractions.all().delete()
		transaction.facts.all().delete()
		transaction.delete()
