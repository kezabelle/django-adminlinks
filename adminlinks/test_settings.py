from settings import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': None,
    }
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'adminlinks',
)

TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.request",
)

SKIP_SOUTH_TESTS = True
SOUTH_TESTS_MIGRATE = False
