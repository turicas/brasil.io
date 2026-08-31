import json
import sys

from sentry_sdk import Scope, capture_exception, capture_message


def report_error(message, context, level, exception=None, tags=None):
    scope = Scope()
    scope.set_context("context", context)
    scope.set_level(level)
    if tags:
        for key, value in tags.items():
            scope.set_tag(key, value)
    if exception is not None:
        capture_exception(error=exception, scope=scope)
    else:
        capture_message(message, scope=scope)
    print(f"{message}: {json.dumps(context, default=str)}", file=sys.stderr)
