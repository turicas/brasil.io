import json

from django.conf import settings
from django_redis import get_redis_connection


def log_blocked_request(request, response_status_code):
    user = getattr(request, "user", None)

    request_data = {
        "query_string": list(request.GET.items()),
        "path": request.path,
        "headers": list(request.headers.items()),
        "response_status_code": response_status_code,
        "user_id": getattr(user, "id", None),
        "http": {key: value for key, value in request.META.items() if key.lower().startswith("http_")},
    }
    if settings.RQ_BLOCKED_REQUESTS_LIST:
        conn = get_redis_connection("default")
        conn.lpush(settings.RQ_BLOCKED_REQUESTS_LIST, json.dumps(request_data))
    else:
        print(f"BLOCKED REQUEST - Response {response_status_code}: {request_data}")
