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

    context = {"title_4xx": status, "message": msg}
    return render(request, "4xx.html", context, status=status)
