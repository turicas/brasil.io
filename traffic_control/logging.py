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


def log_blocked_request(request, response_status_code, extra: dict | None = None):
    """
    Enfileira um request bloqueado para persistência posterior em `BlockedRequest`.

    O conteúdo de `extra` é adicionado a `request_data`.
    """
    request_data = format_request(request, response_status_code)
    if extra:
        request_data.update(extra)
    blocked_requests.lpush(request_data)
