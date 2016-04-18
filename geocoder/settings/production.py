from .base import *

DEBUG = False

ALLOWED_HOSTS = ['geocoder.demozoo.org']

LOGGING = {
	'version': 1,
	'disable_existing_loggers': True,
	'formatters': {
		'standard': {
			'format': '%(asctime)s [%(levelname)s] %(pathname)s: %(message)s'
		},
	},
	'handlers': {
		'default': {
			'level': 'DEBUG',
			'class': 'logging.handlers.RotatingFileHandler',
			'filename': '/home/demozoo/log/geocoder.log',
			'maxBytes': 10485760,
			'backupCount': 500,
			'formatter': 'standard',
		},
		'mail_admins': {
			'level': 'ERROR',
			'filters': [],
			'class': 'django.utils.log.AdminEmailHandler',
		}
	},
	'loggers': {
		'': {
			'handlers': ['default'],
			'level': 'DEBUG',
		},
		'django.request': {
			'handlers': ['default', 'mail_admins'],
			'level': 'DEBUG',
		}
	}
}

try:
	from .local import *
except ImportError:
	pass
