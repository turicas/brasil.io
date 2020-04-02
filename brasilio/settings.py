import os

import environ

from urllib.parse import urlparse
from django.urls import reverse_lazy


root = environ.Path(__file__) - 2
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env('.env')

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='').split(',')
BASE_DIR = root()
DEBUG = env('DEBUG')
PRODUCTION = env('PRODUCTION', bool)
SECRET_KEY = env('SECRET_KEY')
FERNET_KEY = env('FERNET_KEY')


# Application definition
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    # Third-party apps
    'corsheaders',
    'django_extensions',
    'rest_framework',
    'captcha',
    'cachalot',

    # Project apps
    'core',
    'graphs',
    'brasilio_auth',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if DEBUG:
    MIDDLEWARE.append('utils.sqlprint.SqlPrintingMiddleware')
    INSTALLED_APPS += ('naomi',)

ROOT_URLCONF = 'brasilio.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'brasilio.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {
    'default': env.db('DATABASE_URL'),
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True
DATE_FORMAT = "d \\d\\e F \\d\\e Y"
DATETIME_FORMAT = "d \\d\\e F \\d\\e Y \\à\\s H:i:s"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
public_root = root.path('public/')
MEDIA_ROOT = str(public_root.path('media/'))
MEDIA_URL = '/media/'
STATIC_ROOT = str(public_root.path('static/'))
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    str(root.path('static')),
]

# Data-related settings
DATA_URL = env('DATA_URL')

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
}

CORS_ORIGIN_ALLOW_ALL = True


EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_PORT = env('EMAIL_PORT', int, default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default='True').lower() == 'true'
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='contato@brasil.io')
ADMINS = env('ADMINS').strip() or []
if ADMINS:
    ADMINS = [[item.strip() for item in admin.split('|')]
              for admin in ADMINS.split(',')]
if DEBUG:
    EMAIL_FILE_PATH = MEDIA_ROOT
else:
    SENDGRID_API_KEY = env('SENDGRID_API_KEY')


# Neo4J db conf
def get_neo4j_config_dict(neo4j_uri):
    parsed_uri = urlparse(neo4j_uri)
    return {
        'SCHEME': parsed_uri.scheme,
        'HOST': parsed_uri.hostname,
        'PORT': parsed_uri.port,
        'USERNAME': parsed_uri.username,
        'PASSWORD': parsed_uri.password,
    }


NEO4J_CONF = get_neo4j_config_dict(env('GRAPHENEDB_URL'))
NEO4J_BOLT_PORT = int(env('NEO4J_BOLT_PORT', default=39003))


# Auth conf
LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = reverse_lazy('brasilio_auth:login')

RECAPTCHA_PUBLIC_KEY = env('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = env('RECAPTCHA_PRIVATE_KEY')

ROWS_PER_PAGE = env('ROWS_PER_PAGE', int, default=50)

CACHALOT_ENABLED = env('CACHE_ENABLED', bool, default=True)
CACHALOT_UNCACHABLE_TABLES = frozenset(
    (
        "auth_group",
        "auth_group_permissions",
        "auth_permission",
        "auth_user",
        "auth_user_groups",
        "auth_user_user_permissions",
        "brasilio_auth_newslettersubscriber",
        "core_dataset",
        "core_field",
        "core_link",
        "core_table",
        "core_version",
        "django_admin_log",
        "django_content_type",
        "django_migrations",
        "django_session",
    )
)
CACHES = {
    "default": {
        "BACKEND": env('CACHE_BACKEND'),
        "LOCATION": env('CACHE_LOCATION'),
        "OPTIONS": {"CLIENT_CLASS": env('CACHE_CLIENT_CLASS')},
        "KEY_PREFIX": env("CACHE_KEY_PREFIX"),
    }
}
