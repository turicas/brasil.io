from django.conf import settings
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.urls import is_valid_path, resolve
from django_ratelimit import ALL
from django_ratelimit.core import is_ratelimited
from django_ratelimit.exceptions import Ratelimited
from psycopg2.errors import QueryCanceled

from project.utils.errors import report_error
from traffic_control.constants import RATELIMITED_VIEW_ATTR
from traffic_control.util import ratelimit_key

BLOCKED_REQUEST_ATTR = "_blocked_request"


def block_suspicious_requests(get_response):
    def _raise_exception(request):
        setattr(request, BLOCKED_REQUEST_ATTR, True)
        raise Ratelimited()

    def middleware(request):
        # TODO: DISCLAIMER!!! THIS IS A TEMPORARY HACK TO ESCAPE FROM CURRENT "DDOS ATTACK"
        # WE MUST IMPLEMENT RATE LIMIT CONTROL IN NGINX OR CLOUDFARE SO WE DON'T HAVE TO RELY ON DJANGO TO DO THAT
        agent = request.META.get("HTTP_USER_AGENT", "").lower().strip()
        if not agent or agent in settings.BLOCKED_WEB_AGENTS:
            _raise_exception(request)

        path = request.path
        if settings.APPEND_SLASH and not path.endswith("/"):
            path += "/"

        if is_valid_path(path):
            match = resolve(path)
            if getattr(match.func, RATELIMITED_VIEW_ATTR, None):
                # based in ratelimit decorator
                # https://github.com/jsocol/django-ratelimit/blob/main/ratelimit/decorators.py#L13
                if settings.RATELIMIT_ENABLE and is_ratelimited(
                    request=request,
                    group=None,
                    fn=match.func,
                    key=ratelimit_key,
                    rate=settings.RATELIMIT_RATE,
                    method=ALL,
                    increment=True,
                ):
                    _raise_exception(request)

        return get_response(request)

    return middleware


class CatchStatementTimeoutMiddleware:
    """
    Intercepta `statement_timeout` do Postgres para reportar ao Sentry e devolver HTTP 503 na API, em vez de deixar a
    exceção virar 500 não tratado (que dispararia um e-mail para os admins).

    Precisa ser `process_exception`: exceções levantadas em views nunca chegam ao `get_response()` de um middleware,
    porque o Django as converte em resposta 500 antes (`convert_exception_to_response`).

    Não loga em `BlockedRequest` (`statement_timeout` pode acontecer com usuários legítimos afetados pela saturação
    causada por outro abusador da API).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, (QueryCanceled, OperationalError)):
            return None
        if "statement timeout" not in str(exception).lower():
            return None
        report_error(
            "Statement timeout no Postgres",
            context={"path": request.path, "host": request.get_host()},
            level="error",
            exception=exception,
            tags={"kind": "statement_timeout"},
        )
        from_api = request.get_host() == settings.BRASILIO_API_HOST or request.path.startswith("/api/")
        if from_api:
            return JsonResponse(
                {"message": "Serviço temporariamente sobrecarregado. Tente novamente em instantes."},
                status=503,
            )
        return None
