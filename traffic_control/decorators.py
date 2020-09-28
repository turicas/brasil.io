from django.conf import settings
from ratelimit.decorators import ratelimit

from traffic_control.constants import RATELIMITED_VIEW_ATTR
from traffic_control.util import ratelimit_key


def enable_ratelimit(view):
    def view_with_rate_limit(request, *args, **kwargs):
        # cannot use @decorator syntax because reading from settings during import time
        # prevents django.test.override_settings from working as expected.
        # that's why I'm manually decorating the view in this custom view
        return ratelimit(key=ratelimit_key, rate=settings.RATELIMIT_RATE, block=settings.RATELIMIT_ENABLE)(view)(
            request, *args, **kwargs
        )

    setattr(view_with_rate_limit, RATELIMITED_VIEW_ATTR, True)
    return view_with_rate_limit
