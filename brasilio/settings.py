from urllib.parse import urlparse

import environ
import sentry_sdk
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.rq import RqIntegration

root = environ.Path(__file__) - 2
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(".env")

ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="").split(",")
BASE_DIR = root()
DEBUG = env("DEBUG")
PRODUCTION = env("PRODUCTION", bool)
SECRET_KEY = env("SECRET_KEY")
FERNET_KEY = env("FERNET_KEY")


# Application definition
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    # Third-party apps
    "cachalot",
    "captcha",
    "corsheaders",
    "django_extensions",
    "rest_framework",
    "markdownx",
    "django_rq",
    # Project apps
    "core",
    "graphs",
    "brasilio_auth",
    "covid19.apps.Covid19Config",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middlewares.NotLoggedUserFetchFromCacheMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if DEBUG:
    MIDDLEWARE.append("utils.sqlprint.SqlPrintingMiddleware")
    INSTALLED_APPS += ("naomi",)

ROOT_URLCONF = "brasilio.urls"
APPEND_SLASH = True
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "covid19.context_processors.is_covid19_contributor",
            ]
        },
    }
]
WSGI_APPLICATION = "brasilio.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL")}
DB_STATEMENT_TIMEOUT = env("DB_STATEMENT_TIMEOUT", default=20000, cast=int)  # miliseconds


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True
DATE_FORMAT = "d \\d\\e F \\d\\e Y"
DATETIME_FORMAT = "d \\d\\e F \\d\\e Y \\à\\s H:i:s"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
public_root = root.path("public/")
MEDIA_ROOT = env("MEDIA_ROOT", default=str(public_root.path("media/")))
MEDIA_URL = "/media/"
STATIC_ROOT = str(public_root.path("static/"))
STATIC_URL = "/static/"
STATICFILES_STORAGE = env("STATICFILES_STORAGE")
STATICFILES_DIRS = [str(root.path("static"))]

DEFAULT_FILE_STORAGE = env("DEFAULT_FILE_STORAGE")

# django-storage configurations for AWS file upload
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_DEFAULT_ACL = env("AWS_DEFAULT_ACL")
AWS_BUCKET_ACL = env("AWS_BUCKET_ACL")
AWS_AUTO_CREATE_BUCKET = env("AWS_AUTO_CREATE_BUCKET")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN")
AWS_IS_GZIPPED = env("AWS_IS_GZIPPED")
GZIP_CONTENT_TYPES = env("GZIP_CONTENT_TYPES")

CACHE_INTERVAL = 900  # 15 minutes
MINIO_STORAGE_ENDPOINT = AWS_S3_ENDPOINT_URL.replace("https://", "").replace("/", "")
MINIO_STORAGE_ACCESS_KEY = AWS_ACCESS_KEY_ID
MINIO_STORAGE_SECRET_KEY = AWS_SECRET_ACCESS_KEY
MINIO_STORAGE_USE_HTTPS = True
MINIO_STORAGE_MEDIA_BUCKET_NAME = env("MINIO_STORAGE_MEDIA_BUCKET_NAME")
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = AWS_AUTO_CREATE_BUCKET
MINIO_STORAGE_STATIC_BUCKET_NAME = env("MINIO_STORAGE_STATIC_BUCKET_NAME")
MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = AWS_AUTO_CREATE_BUCKET

# Data-related settings
DATA_URL = env("DATA_URL")

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    'EXCEPTION_HANDLER': 'api.handlers.api_exception_handler',
}

THROTTLING_RATE = env("THROTTLING_RATE")

if THROTTLING_RATE:
    REST_FRAMEWORK.update({
        "DEFAULT_THROTTLE_CLASSES": [
            "rest_framework.throttling.AnonRateThrottle",
            "rest_framework.throttling.UserRateThrottle"
        ],
        "DEFAULT_THROTTLE_RATES": {
            "anon": THROTTLING_RATE,
            "user": THROTTLING_RATE,
        }
    })

CORS_ORIGIN_ALLOW_ALL = True


EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_PORT = env("EMAIL_PORT", int, default=587)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default="True").lower() == "true"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="contato@brasil.io")
ADMINS = env("ADMINS").strip() or []
if ADMINS:
    ADMINS = [[item.strip() for item in admin.split("|")] for admin in ADMINS.split(",")]
if DEBUG:
    EMAIL_FILE_PATH = MEDIA_ROOT
else:
    SENDGRID_API_KEY = env("SENDGRID_API_KEY")


# Neo4J db conf
def get_neo4j_config_dict(neo4j_uri):
    parsed_uri = urlparse(neo4j_uri)
    return {
        "SCHEME": parsed_uri.scheme,
        "HOST": parsed_uri.hostname,
        "PORT": parsed_uri.port,
        "USERNAME": parsed_uri.username,
        "PASSWORD": parsed_uri.password,
    }


NEO4J_CONF = get_neo4j_config_dict(env("GRAPHENEDB_URL"))
NEO4J_BOLT_PORT = int(env("NEO4J_BOLT_PORT", default=39003))


# Auth conf
LOGOUT_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = reverse_lazy("brasilio_auth:login")

RECAPTCHA_PUBLIC_KEY = env("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = env("RECAPTCHA_PRIVATE_KEY")

ROWS_PER_PAGE = env("ROWS_PER_PAGE", int, default=50)

REDIS_URL = env("REDIS_URL")
CACHALOT_ENABLED = env("CACHE_ENABLED", bool, default=True)
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = CACHE_INTERVAL
CACHE_MIDDLEWARE_KEY_PREFIX = "non_logged_user_"
CACHALOT_CACHE = "default"
CACHES = {
    "default": {
        "BACKEND": env("CACHE_BACKEND"),
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": env("CACHE_CLIENT_CLASS")},
        "KEY_PREFIX": env("CACHE_KEY_PREFIX"),
    }
}
if DEBUG:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache",}}

# django-rq config
RQ_QUEUES = {"default": {"URL": REDIS_URL, "DEFAULT_TIMEOUT": 500,}}
RQ = {
    "DEFAULT_RESULT_TTL": 60 * 60 * 24,  # 24-hours
}

if not DEBUG:
    RQ_QUEUES["default"]["WORKER_CLASS"] = "brasilio.worker.SentryAwareWorker"


# Covid19 import settings
COVID_IMPORT_PERMISSION_PREFIX = "can_import_covid_state_"

# RockecChat config
ROCKETCHAT_BASE_URL = env("ROCKETCHAT_BASE_URL")
ROCKETCHAT_USER_ID = env("ROCKETCHAT_USER_ID")
ROCKETCHAT_AUTH_TOKEN = env("ROCKETCHAT_AUTH_TOKEN")

# Sentry config
SENTRY_DSN = env("SENTRY_DSN")
sentry_sdk.init(
    SENTRY_DSN, integrations=[DjangoIntegration(), RqIntegration()], send_default_pii=True,
)
