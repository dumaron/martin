import os

environment = os.environ.get('DJANGO_ENVIRONMENT', 'dev')

if environment == 'dev':
	from .dev import *
else:
	from .prod import *
