from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from elections import page_counter
from elections.filters import CandidacyFilterSet
from elections.models import Candidacy, CandidacyMetadata
from elections.serializers import DetailCandidacySerializer, ListCandidacySerializer
from elections.suggestions import create_search_suggestions
from elections.title_utils import candidacy_list_title


def filter_selected_fields(filter_data):
    data = filter_data.dict()
    data.pop("format", None)
    for key in ("cargo", "uf", "partido"):
        if data.get(key) is None:
            data[key] = "Todos"

    if data.get("t") is None:
        data["t"] = "cidade"

    data.pop("ano", None)

    return data


def candidacy_list(request):
    # TODO: safe coercion
    page_size = int(request.GET.get("page_size", 40))
    filter_set = CandidacyFilterSet(request.GET, queryset=Candidacy.objects.all())
    paginator = Paginator(filter_set.qs, page_size)
    page = request.GET.get("page", 1)
    objs = paginator.page(page).object_list
    serializer = ListCandidacySerializer(objs, many=True)
    metadata = CandidacyMetadata.objects.first().data

    selected_filter_fields = filter_selected_fields(filter_set.data)
    title = candidacy_list_title(
        **selected_filter_fields,
        ano="2024",
        ano_inicio=Candidacy.first_year()
    )

    data = {
        "items": serializer.data,
        "number": page,
        "num_pages": paginator.num_pages,
        "page_size": page_size,
        "filters": selected_filter_fields,
        "title": title,
        "page_counter": page_counter.counter(
            page=int(page),
            page_size=page_size,
            total=Candidacy.get_total()
        )
    }

    if request.GET.get("format") == "json":
        return JsonResponse(data, safe=False)

    data["metadata"] = metadata

    return render(request, "elections/elections.html", context={"data": data})


def politic(request, ano, uf, municipio, cargo, nome):
    candidacy = get_object_or_404(
        Candidacy,
        ano=ano,
        sigla_unidade_federativa__iexact=uf,
        municipio_slug=municipio,
        cargo_slug=cargo,
        nome_urna_slug=nome,
    )
    metadata = CandidacyMetadata.objects.first().data
    serializer = DetailCandidacySerializer(candidacy)
    data = {
        "item": serializer.data,
        "info_list": candidacy.info_list,
        "details_list": [
            {
                "label": "Mídias Sociais",
                "type": "social_networks",
                "collapsed": True,
                "value": candidacy.social_networks_list(),
            },
        ]
    }
    if request.GET.get("format") == "json":
        return JsonResponse(data=data)

    data["metadata"] = metadata

    return render(request, "elections/politic.html", context={"data": data})

def home(request):
    metadata = CandidacyMetadata.objects.first().data
    context = {
        "data": {
            "metadata": metadata,
            "suggestions": create_search_suggestions(),
        }
    }
    return render(request, "elections/home.html", context)


def about(request, state=None):
    metadata = CandidacyMetadata.objects.first().data
    context = {
        "data": {
            "metadata": metadata,
            "title": "Sobre o Brasil.IO Eleições",
            "text_list": [
                {
                    "label": "O que é",
                    "value": "O Brasil.IO Eleições é uma plataforma sem fins lucrativos que disponibiliza informações públicas relevantes sobre os candidatos às eleições municipais de 2024. A plataforma foi criada para facilitar o acesso a essas informações para eleitores, jornalistas e pesquisadores, contribuindo para um processo eleitoral mais informativo e consciente."
                },
                {
                    "label": "Fontes dos dados",
                    "value": "Os dados divulgados no Brasil.IO Eleições são provenientes de fontes de dados públicas, como o Portal de Dados Abertos do Tribunal Superior Eleitoral (TSE) e o Portal de Dados Abertos da Receita Federal.<br><br> Além dessas fontes, informações adicionais são fornecidas pelos órgãos públicos em resposta a solicitações de acesso à informação, com base na Lei Federal 12.527/2011 (Lei de Acesso à Informação).<br><br> Como a fonte primária de todos os dados divulgados são órgãos públicos, a plataforma considera que os dados divulgados por essas fontes são corretos em relação ao seu conteúdo."
                },
                {
                    "label": "Tratamento dos dados e legislação",
                    "value": "O uso e disponibilização dos dados pelo Brasil.IO Eleições está em total conformidade com a legislação brasileira. De acordo com o art. 29, caput e § 1º da Lei Federal 14.129/2021, dados públicos obtidos com base na Lei de Acesso à informação podem ser utilizados de forma livre e irrestrita pela sociedade, sendo legítimo e lícito o seu tratamento com base, entre outros, no art. 7o, II e IX da Lei Federal 13.709/2018 (Lei Geral de Proteção de Dados - LGPD).<br><br> A plataforma prioriza a transparência e o acesso à informação, garantindo que os dados sejam utilizados de forma ética e responsável. O Brasil.IO Eleições não realiza nenhum tipo de alteração no conteúdo dos dados originais. Os tratamentos realizados têm como foco garantir que as informações sejam apresentadas de forma clara e organizada, facilitando a compreensão e o acesso por parte do público."
                },
                {
                    "label": "Política de privacide",
                    "value": "<a href='/eleicoes/politica_de_privacidade' target='_blank'>Clique aqui</a> para conhecer a política de privacidade do Brasil.IO Eleições."
                },
                {
                    "label": "Contato",
                    "value": "Em caso de dúvidas sobre a plataforma ou necessidade de solicitar retificação de dados, entre em contato por meio <a href='https://brasil.io/contato/'>deste formulário</a>. Para solicitações de retificação, descreva de forma clara e fundamentada o dado que precisa ser corrigido."
                }
            ],
        }
    }
    return render(request, "elections/generic_text.html", context)


def privacy_policy(request, state=None):
    metadata = CandidacyMetadata.objects.first().data
    context = {
        "data": {
            "metadata": metadata,
            "title": "Política de privacidade",
            "text_list": [
                {
                    "label": "Sua privacidade no Brasil.IO Eleições",
                    "value": "Respeitamos sua privacidade e estamos comprometidos em proteger as informações pessoais que você possa fornecer enquanto navega em nosso site. Esta política de privacidade explica como coletamos e usamos seus dados quando você visita nosso site, especialmente em relação ao Google Analytics."
                },
                {
                    "label": "Coleta de Informações",
                    "value": "Utilizamos o Google Analytics para coletar informações sobre como os visitantes utilizam nosso site. Isso inclui dados como o seu endereço IP, tipo de navegador, páginas visitadas, tempo gasto em cada página e outros dados estatísticos."
                },
                {
                    "label": "Uso de Informações",
                    "value": "As informações coletadas pelo Google Analytics são usadas para analisar tendências de uso do site, gerar relatórios estatísticos e melhorar a experiência do usuário em nosso site. Esses dados são tratados de forma agregada e anônima, não sendo associados a nenhuma informação pessoal identificável."
                },
                {
                    "label": "Cookies",
                    "value": "O Google Analytics utiliza cookies para coletar informações anônimas. Os cookies são pequenos arquivos de texto armazenados no seu dispositivo para ajudar a analisar o uso do site. Você pode optar por desativar o uso de cookies nas configurações do seu navegador, mas isso pode afetar a funcionalidade do site."
                },
                {
                    "label": "Compartilhamento de Informações",
                    "value": "Não compartilhamos informações pessoalmente identificáveis coletadas pelo Google Analytics com terceiros, exceto quando exigido por lei ou decisão judicial."
                },
                {
                    "label": "Segurança",
                    "value": "Implementamos medidas de segurança para proteger suas informações contra acesso não autorizado ou uso indevido."
                },
                {
                    "label": "Alterações nesta Política",
                    "value": "Esta política de privacidade pode ser atualizada periodicamente para refletir mudanças em nossas práticas de informações. Recomendamos que você revise esta política regularmente para estar ciente de como estamos protegendo suas informações."
                },
                {
                    "label": "Contato",
                    "value": "Se você tiver dúvidas sobre esta política de privacidade ou sobre nossas práticas de informações, entre em contato por meio <a href='https://brasil.io/contato/' target='_blank'>deste formulário</a>."
                }
            ],
        }
    }
    return render(request, "elections/generic_text.html", context)


def candidacy_redirect_2024(request):
    return redirect("elections:candidacy_list")
