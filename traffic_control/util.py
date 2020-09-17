def get_ip(request):
    ip = request.META.get("HTTP_CF_CONNECTING_IP", "").strip()
    if not ip:
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").strip()
        if not ip:
            ip = request.META.get("REMOTE_ADDR", "").strip()
        else:
            ip = ip.split(",")[0]
    return ip


def ratelimit_key(group, request):
    ip = get_ip(request)
    request.META.get("HTTP_USER_AGENT", "")
    # key = f"{ip}:{agent}"
    key = ip
    return key
