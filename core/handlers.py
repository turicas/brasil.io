from django.shortcuts import render
from ratelimit.exceptions import Ratelimited

rate_limit_msg = """
<p>Você atingiu o limite de requisições e, por isso, essa requisição foi bloqueada. Caso você precise acessar várias páginas de um dataset, por favor, baixe o dataset completo em vez de percorrer várias páginas na interface (o link para baixar o arquivo completo encontra-se na <a href="https://brasil.io/datasets/">página do dataset</a>).</p>
<p>Utilizar a interface do Brasil.io via web crawlers e de maneira não otimizada onera muito nossos servidores e atrapalha a experiência de outros usuários. Se o abuso continuar, precisaremos restringir ainda mais os limites de requisições e não gostaríamos de fazer isso.</p>
<p>Lembre-se: o Brasil.IO é um projeto colaborativo, desenvolvido por voluntários e mantido por financiamento coletivo, você pode doar na <a href="https://apoia.se/brasilio">página do projeto no Apoia.se</a>.</p>
""".strip()


def handler_403(request, exception):
    """
    Handler to deal with Ratelimited exception as exepcted. Reference:
    https://django-ratelimit.readthedocs.io/en/stable/usage.html#exceptions
    """
    status = 403
    msg = "Oops! Parece que você não tem permissão para acessar essa página."

    if isinstance(exception, Ratelimited):
        status, msg = 429, rate_limit_msg

        # TODO: DISCLAIMER! This is a technique to slow down attackers: we make
        # them use bandwidth (so attacking the website becomes expensive). This
        # will add from 1MB to 100MB of garbage inside the HTML as a comment;
        # since the data is random, gzip won't help the attacker here.
        import base64
        import json
        import os
        import random
        from django_redis import get_redis_connection

        conn = get_redis_connection("default")

        request_data = {
            "query_string": list(request.GET.items()),
            "path": request.path,
            "headers": list(request.headers.items()),
        }
        conn.lpush("blocked", json.dumps(request_data))

        data = base64.b64encode(os.urandom(random.randint(1, 10) * 1024 * 1024)).decode("ascii")
        msg += "<!-- " + data + " -->"

    context = {"title_4xx": status, "message": msg}
    return render(request, "4xx.html", context, status=status)
