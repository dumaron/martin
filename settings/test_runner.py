from argparse import ArgumentParser

from django.test.runner import DiscoverRunner


class ColocatedTestRunner(DiscoverRunner):
	@classmethod
	def add_arguments(cls, parser: ArgumentParser) -> None:
		super().add_arguments(parser)
		parser.set_defaults(pattern='*test*.py')
