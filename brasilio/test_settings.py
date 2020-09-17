from pathlib import Path

from .settings import *  # noqa

for queue in RQ_QUEUES.values():  # noqa
    queue["ASYNC"] = False


block_middleware = "traffic_control.middlewares.block_suspicious_requests"
if block_middleware in MIDDLEWARE:
    MIDDLEWARE.remove(block_middleware)

SAMPLE_SPREADSHEETS_DATA_DIR = Path(BASE_DIR).joinpath("covid19", "tests", "data")  # noqa
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache",}}  # noqa
RQ_BLOCKED_REQUESTS_LIST = ""

RATELIMIT_ENABLE = False  # noqa
