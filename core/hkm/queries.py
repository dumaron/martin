from core.hkm.models import Fact


def entities():
	"""
	Identifiers known to the knowledge base, derived from current facts.

	There is no entities table — an entity exists by being mentioned. For now this only derives from
	subjects; the full derivation would also union objects of 'reference' predicates.
	"""
	return Fact.objects.current().values_list('subject', flat=True).distinct().order_by('subject')
