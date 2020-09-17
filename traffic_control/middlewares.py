from django.conf import settings
from ratelimit.exceptions import Ratelimited


def block_suspicious_requests(get_response):

    def middleware(request):
        # TODO: DISCLAIMER!!! THIS IS A TEMPORARY HACK TO ESCAPE FROM CURRENT "DDOS ATTACK"
        # WE MUST IMPLEMENT RATE LIMIT CONTROL IN NGINX OR CLOUDFARE SO WE DON'T HAVE TO RELY ON DJANGO TO DO THAT
        agent = request.META.get("HTTP_USER_AGENT", "").lower().strip()
        if not agent or agent in settings.BLOCKED_WEB_AGENTS:
            raise Ratelimited()

        return get_response(request)

    return middleware
