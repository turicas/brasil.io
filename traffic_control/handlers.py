import base64
import os
import random
from functools import lru_cache

from django.shortcuts import render
from django.urls import reverse
from ratelimit.exceptions import Ratelimited
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler

from api.versioning import redirect_from_older_version
from traffic_control.logging import log_blocked_request

rate_limit_msg = """
<p>Você atingiu o limite de requisições e, por isso, essa requisição foi bloqueada. Caso você precise acessar várias páginas de um dataset, por favor, baixe o dataset completo em vez de percorrer várias páginas na interface (o link para baixar o arquivo completo encontra-se na <a href="https://brasil.io/datasets/">página do dataset</a>).</p>
<p>Utilizar a interface do Brasil.io via web crawlers e de maneira não otimizada onera muito nossos servidores e atrapalha a experiência de outros usuários. Se o abuso continuar, precisaremos restringir ainda mais os limites de requisições e não gostaríamos de fazer isso.</p>
<p>Lembre-se: o Brasil.IO é um projeto colaborativo, desenvolvido por voluntários e mantido por financiamento coletivo, você pode doar na <a href="https://apoia.se/brasilio">página do projeto no Apoia.se</a>.</p>
""".strip()

api_throtthling_msg = """
Você atingiu o limite de requisições e, por isso, essa requisição foi bloqueada. Caso você precise acessar várias páginas de um dataset, por favor, baixe o dataset completo em vez de percorrer várias páginas na API (o link para baixar o arquivo completo encontra-se na página do dataset, em https://brasil.io/datasets/).
Utilizar a API desnecessariamente e de maneira não otimizada onera muito nossos servidores e atrapalha a experiência de outros usuários. Se o abuso continuar, precisaremos restringir ainda mais a API e não gostaríamos de fazer isso.
Lembre-se: o Brasil.IO é um projeto colaborativo, desenvolvido por voluntários e mantido por financiamento coletivo, você pode doar para o projeto em: https://apoia.se/brasilio
""".strip()


@lru_cache(maxsize=10)
def gen_big_payload(msg_size):
    data = base64.b64encode(os.urandom(msg_size * 1024 * 1024)).decode("ascii")
    return "<!-- " + data + " -->"


def handler_403(request, exception):
    """
    Handler to deal with Ratelimited exception as exepcted. Reference:
    https://django-ratelimit.readthedocs.io/en/stable/usage.html#exceptions
    """
    status = 403
    msg = "Oops! Parece que você não tem permissão para acessar essa página."

    if isinstance(exception, Ratelimited):
        status, msg = 429, rate_limit_msg
        msg += gen_big_payload(random.randint(1, 10))

    log_blocked_request(request, status)
    context = {"title_4xx": status, "message": msg}
    return render(request, "4xx.html", context, status=status)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    status_code = getattr(response, "status_code", None)

    redirect = redirect_from_older_version(exc)
    if redirect:
        return redirect

    if isinstance(exc, Throttled):
        custom_response_data = {"message": api_throtthling_msg, "available_in": f"{exc.wait} seconds"}
        response.data = custom_response_data

    if 400 <= status_code < 500:
        log_blocked_request(context["request"], status_code)
        if 401 == status_code:
            url = reverse("brasilio_auth:list_api_tokens")
            msg = f"As credenciais de autenticação não foram fornecidas. Acesse https://brasil.io{url} para gerenciar suas chaves de acesso a API."
            response.data = {"message": msg}

    return response
