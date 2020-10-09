from pathlib import Path

from .settings import *  # noqa

for queue in RQ_QUEUES.values():  # noqa
    queue["ASYNC"] = False

SAMPLE_SPREADSHEETS_DATA_DIR = Path(BASE_DIR).joinpath("covid19", "tests", "data")  # noqa
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache",}}  # noqa
RQ_BLOCKED_REQUESTS_LIST = ""

RATELIMIT_ENABLE = False  # noqa
TEMPLATE_STRING_IF_INVALID = "%%%Invalid variable%%%"  # noqa
TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = TEMPLATE_STRING_IF_INVALID  # noqa
ENABLE_API_AUTH = True
