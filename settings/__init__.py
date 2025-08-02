import os

environment = os.environ.get('DJANGO_ENVIRONMENT', 'dev')

if environment == 'dev':
	from .prod import *
else:
	from .dev import *
