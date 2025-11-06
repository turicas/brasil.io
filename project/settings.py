import sentry_sdk
from decouple import Csv, config
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.rq import RqIntegration

from .base_settings import *  # noqa

API_ROOT_URLCONF = "project.api_urls"
APP_HOST = config("APP_HOST", default="brasil.io")
AUTHENTICATION_BACKENDS = ["brasilio_auth.auth_backend.UsernameOrEmailBackend"]
BLOCKED_AGENTS = config("BLOCKED_AGENTS", cast=Csv(), default="")
BLOCKED_WEB_AGENTS = [a.lower() for a in config("BLOCKED_WEB_AGENTS", cast=Csv(), default="")]
BRASILIO_API_HOST = config("BRASILIO_API_HOST", default="api.brasil.io")
DATABASE_STATEMENT_TIMEOUT = config("DATABASE_STATEMENT_TIMEOUT", default=25000, cast=int)  # miliseconds
DATETIME_FORMAT = "d \\d\\e F \\d\\e Y \\à\\s H:i:s"
DATE_FORMAT = "d \\d\\e F \\d\\e Y"
FERNET_KEY = config("FERNET_KEY")
LANGUAGE_CODE = "pt-br"
MEDIA_ROOT = config("MEDIA_ROOT", default=str(BASE_DIR / "public" / "media"))
MEDIA_URL = "/media/"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_DOMAIN = config("SESSION_COOKIE_DOMAIN", default=None)  # ".brasil.io"  # wildcard brasil.io subdomains
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True

TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]
TEMPLATES[0]["OPTIONS"]["context_processors"].extend(
    [
        "core.context_processors.template_settings",
        "covid19.context_processors.is_covid19_contributor",
    ]
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "cachalot",
    "corsheaders",
    "django_extensions",
    "django_recaptcha",
    "django_registration",
    "django_rq",
    "markdownx",
    "rangefilter",
    "rest_framework",
    "storages",
    # Project apps
    "api",
    "core",
    "brasilio_auth",
    "covid19.apps.Covid19Config",
    "dashboard",
    "traffic_control",
]
MIDDLEWARE = [
    "project.middlewares.host_based_url_conf",
    "django.middleware.security.SecurityMiddleware",
    "traffic_control.middlewares.block_suspicious_requests",
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

env_type_abbrev = {"development": "dev", "staging": "stg", "production": None}[ENV_TYPE]
EMAIL_SUBJECT_PREFIX = f"[{env_type_abbrev}] " if ENV_TYPE != "production" else ""


# Data-related settings
AWS_BUCKET_ACL = config("AWS_BUCKET_ACL")
AWS_DEFAULT_ACL = config("AWS_DEFAULT_ACL")
AWS_IS_GZIPPED = config("AWS_IS_GZIPPED")
AWS_S3_ACCESS_KEY_ID = config("AWS_S3_ACCESS_KEY_ID")
AWS_S3_DATASETS_BUCKET_NAME = config("AWS_S3_DATASETS_BUCKET_NAME")
AWS_S3_DATASET_DOWNLOAD_CHUNK_SIZE = config("AWS_S3_DATASET_DOWNLOAD_CHUNK_SIZE", cast=int, default=8388608)
AWS_S3_DATASET_SHA512SUMS_FILENAME = config("AWS_S3_DATASET_SHA512SUMS_FILENAME", default="SHA512SUMS")
AWS_S3_DATASET_TABLES_FILES_LIST_FILENAME = config(
    "AWS_S3_DATASET_TABLES_FILES_LIST_FILENAME", default="_meta/list.html"
)
AWS_S3_SECRET_ACCESS_KEY = config("AWS_S3_SECRET_ACCESS_KEY")
AWS_S3_URL_PROTOCOL = config("AWS_S3_URL_PROTOCOL", default="https:")
DATA_URL = config("DATA_URL")
GZIP_CONTENT_TYPES = config("GZIP_CONTENT_TYPES")


# API/DRF settings
CORS_ORIGIN_ALLOW_ALL = True
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "EXCEPTION_HANDLER": "traffic_control.handlers.api_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["api.permissions.ApiIsAuthenticated"],
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
}
MAX_NUM_API_TOKEN_PER_USER = config("MAX_NUM_API_TOKEN_PER_USER", cast=int, default=10)
ENABLE_API_AUTH = config("ENABLE_API_AUTH", cast=bool, default=False)
THROTTLING_RATE = config("THROTTLING_RATE")
if THROTTLING_RATE:
    REST_FRAMEWORK.update(
        {
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
                "rest_framework.throttling.UserRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "anon": THROTTLING_RATE,
                "user": THROTTLING_RATE,
            },
        }
    )
API_DEMO_URL = config("API_DEMO_URL", default="https://gist.github.com/turicas/3e3621d61415e3453cd03a1997f7473f")
API_KEYS_BLOGPOST_URL = config("API_KEYS_BLOGPOST_URL", default="https://blog.brasil.io/")
RATELIMIT_ENABLE = config("RATELIMIT_ENABLE", cast=bool, default=False)
RATELIMIT_RATE = config(
    "RATELIMIT_RATE", default="10/m"
)  # we have to force a default value, otherwise django-ratelimit breaks our app


# Auth conf
ACCOUNT_ACTIVATION_DAYS = config("ACCOUNT_ACTIVATION_DAYS", cast=int, default=7)
REGISTRATION_SALT = config("REGISTRATION_SALT", default=SECRET_KEY)
REGISTRATION_OPEN = config("REGISTRATION_OPEN", cast=bool, default=True)
LOGOUT_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = reverse_lazy("brasilio_auth:login")
DISABLE_RECAPTCHA = config("DISABLE_RECAPTCHA", cast=bool, default=False)
RECAPTCHA_PUBLIC_KEY = config("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = config("RECAPTCHA_PRIVATE_KEY")


# Rows/export to CSV
ROWS_PER_PAGE = config("ROWS_PER_PAGE", cast=int, default=50)
CSV_EXPORT_MAX_ROWS = config("CSV_EXPORT_MAX_ROWS", default=10_000, cast=int)


# Caching
CACHE_INTERVAL = 900  # 15 minutes
CACHALOT_ENABLED = config("CACHE_ENABLED", cast=bool, default=True)
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = CACHE_INTERVAL
CACHE_MIDDLEWARE_KEY_PREFIX = "non_logged_user_"
CACHALOT_CACHE = "default"
CACHES = {
    "default": {
        "BACKEND": config("CACHE_BACKEND"),
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": config("CACHE_CLIENT_CLASS")},
        "KEY_PREFIX": config("CACHE_KEY_PREFIX"),
    }
}

# django-rq config
RQ_QUEUES = {"default": {"URL": REDIS_URL, "DEFAULT_TIMEOUT": 500}}
RQ = {"DEFAULT_RESULT_TTL": 60 * 60 * 24}
RQ_BLOCKED_REQUESTS_LIST = config("RQ_BLOCKED_REQUESTS_LIST")
if not DEBUG:
    RQ_QUEUES["default"]["WORKER_CLASS"] = "project.worker.SentryAwareWorker"


# Covid19 import settings
COVID_IMPORT_PERMISSION_PREFIX = "can_import_covid_state_"
COVID_19_ADMIN_GROUP_NAME = "Admins Covid-19"
COVID_19_STATE_TOTALS_URL = (
    "https://docs.google.com/spreadsheets/d/17mmfgPAcVCeHW3548BlFtuurAvF3jeffRVO1NW7rVgQ/export?format=csv"
)
COVID19_AUTO_IMPORT_USER = "robo_covid19"


# RockecChat robot
ROCKETCHAT_BASE_URL = config("ROCKETCHAT_BASE_URL")
ROCKETCHAT_USERNAME = config("ROCKETCHAT_USERNAME")
ROCKETCHAT_PASSWORD = config("ROCKETCHAT_PASSWORD")


# Cloudflare
CLOUDFLARE_AUTH_EMAIL = config("CLOUDFLARE_AUTH_EMAIL")
CLOUDFLARE_AUTH_KEY = config("CLOUDFLARE_AUTH_KEY")
CLOUDFLARE_ACCOUNT_NAME = config("CLOUDFLARE_ACCOUNT_NAME")
CLOUDFLARE_BLOCKED_IPS_RULE = config("CLOUDFLARE_BLOCKED_IPS_RULE")


# Últimas atualizações (home)
NUM_RECENT_ACTIVITES_HOMEPAGE = config("NUM_RECENT_ACTIVITES_HOMEPAGE", cast=int, default=5)
DAYS_RANGE_RECENT_ACTIVITES_HOMEPAGE = config("DAYS_RANGE_RECENT_ACTIVITES_HOMEPAGE", cast=int, default=30)


if SENTRY_DSN:
    sentry_sdk.init(
        SENTRY_DSN,
        integrations=[DjangoIntegration(), RqIntegration()],
        send_default_pii=True,
    )
    # TODO: add environment
