import json
from django_redis import get_redis_connection

from django.conf import settings


def log_blocked_request(request, response_status_code):
    user = getattr(request, "user", None)

    request_data = {
        "query_string": list(request.GET.items()),
        "path": request.path,
        "headers": list(request.headers.items()),
        "response_status_code": response_status_code,
        "user_id": getattr(user, "id", None),
    }
    if settings.RQ_BLOCKED_REQUESTS_LIST:
        conn = get_redis_connection("default")
        conn.lpush(settings.RQ_BLOCKED_REQUESTS_LIST, json.dumps(request_data))
    else:
        print(f"BLOCKED REQUEST - Response {response_status_code}: {request_data}")
