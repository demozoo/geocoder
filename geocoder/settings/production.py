from .base import *

DEBUG = False

ALLOWED_HOSTS = ['geocoder.demozoo.org']

try:
	from .local import *
except ImportError:
	pass
