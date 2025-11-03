import json
import sys

from sentry_sdk import Scope, capture_message


def report_error(message, context, level):
    scope = Scope()
    scope.set_context("context", context)
    capture_message(message, level=level, scope=scope)
    print(f"{message}: {json.dumps(context, default=str)}", file=sys.stderr)
