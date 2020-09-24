from traffic_control.blocked_list import blocked_requests


def format_request(request, response_status_code):
    user = getattr(request, "user", None)

    request_data = {
        "query_string": list(request.GET.items()),
        "path": request.path,
        "headers": list(request.headers.items()),
        "response_status_code": response_status_code,
        "user_id": getattr(user, "id", None),
        "http": {key: value for key, value in request.META.items() if key.lower().startswith("http_")},
    }
    request_data["http"]["remote-addr"] = request.META.get("REMOTE_ADDR", "").strip()
    return request_data


def log_blocked_request(request, response_status_code):
    request_data = format_request(request, response_status_code)
    blocked_requests.lpush(request_data)
