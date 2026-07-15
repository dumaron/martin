from collections.abc import Iterable
from itertools import starmap

from django.db import transaction as db_transaction
from django.utils import timezone

from core.hkm.models import Fact, Retraction, Transaction
from core.utils.fp import lmap


def create_draft_transaction(
	facts: Iterable[tuple[str, str, str]],
	retractions: Iterable[int] = (),
	description: str = '',
) -> Transaction:
	"""
	Saves the input facts and retractions as a draft transaction in the database
	"""
	with db_transaction.atomic():
		draft = Transaction.objects.create(description=description or None)
		Fact.objects.bulk_create(
			starmap(
				lambda subject, predicate, value: Fact(
					subject=subject, predicate=predicate, object=value, transaction=draft
				),
				facts,
			)
		)
		Retraction.objects.bulk_create(
			lmap(lambda fact_id: Retraction(fact_id=fact_id, transaction=draft), retractions)
		)
	return draft


def update_draft(
	transaction: Transaction,
	facts: Iterable[tuple[str, str, str]],
	retractions: Iterable[int] = (),
	description: str = '',
) -> Transaction:
	"""
	Replace the staged contents of a draft wholesale. Only draft transactions can be updated.
	"""
	# Applied transactions are immutable history and must not be updated
	if transaction.applied_at is not None:
		raise ValueError('Cannot update a transaction that has already been applied')

	with db_transaction.atomic():
		# Old retractions must go before the new ones are staged: the OneToOne on Retraction means a fact
		# re-selected for retraction would otherwise collide with its own previous staging.
		transaction.retractions.all().delete()
		transaction.facts.all().delete()
		Fact.objects.bulk_create(
			Fact(subject=subject, predicate=predicate, object=value, transaction=transaction)
			for subject, predicate, value in facts
		)
		Retraction.objects.bulk_create(
			Retraction(fact_id=fact_id, transaction=transaction) for fact_id in retractions
		)
		transaction.description = description or None
		transaction.save(update_fields=['description'])

	return transaction


def apply_transaction(transaction):
	# Commit a draft by stamping `applied_at`; from then on its facts count as current. Re-applying is a no-op.
	if transaction.applied_at is None:
		transaction.applied_at = timezone.now()
		transaction.save(update_fields=['applied_at'])
	return transaction


def discard_draft(transaction):
	"""
	Mark a transaction as discarded. Only draft transactions can be discarded.
	"""
	# Applied transactions are immutable history and must not be discarded
	if transaction.applied_at is not None:
		raise ValueError('Cannot discard a transaction that has already been applied')

	with db_transaction.atomic():
		# Retractions first: a fact protected by a retraction can't be deleted, and the staged retractions
		# point at facts we want to leave current.
		transaction.retractions.all().delete()
		transaction.facts.all().delete()
		transaction.delete()
