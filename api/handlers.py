from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled


throtthling_msg = """
Você atingiu o limite de requisições e, por isso, essa requisição foi bloqueada. Caso você precise acessar várias páginas de um dataset, por favor, baixe o dataset completo em vez de percorrer várias páginas na API (o link para baixar o arquivo completo encontra-se na página do dataset, em https://brasil.io/datasets/).
Utilizar a API desnecessariamente e de maneira não otimizada onera muito nossos servidores e atrapalha a experiência de outros usuários. Se o abuso continuar, precisaremos restringir ainda mais a API e não gostaríamos de fazer isso.
Lembre-se: o Brasil.IO é um projeto colaborativo, desenvolvido por voluntários e mantido por financiamento coletivo, você pode doar para o projeto em: https://apoia.se/brasilio
""".strip()


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled):
        custom_response_data = {
            'message': throtthling_msg,
            'available_in': f'{exc.wait} seconds'
        }
        response.data = custom_response_data

    return response
