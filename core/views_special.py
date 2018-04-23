from django.contrib.postgres.search import SearchQuery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.models import Dataset


def companies(request):
    Socios = Dataset.objects.get(slug='socios-brasil').get_last_data_model()
    result = []
    search_query = request.GET.get('q')

    if search_query:
        result = Socios.objects.filter(search_data=SearchQuery(search_query))\
                               .values_list('cnpj_empresa', 'nome_empresa')\
                               .distinct()\
                               .order_by('nome_empresa')

    context = {
        'result': result,
        'search_query': search_query,
    }
    return render(request, 'specials/companies.html', context)

def company_detail(request, document):
    document = document.replace('.', '').replace('-', '').replace('/', '').strip()
    Socios = Dataset.objects.get(slug='socios-brasil').get_last_data_model()
    GastosDeputados = Dataset.objects.get(slug='gastos-deputados').get_last_data_model()
    GastosDiretos = Dataset.objects.get(slug='gastos-diretos').get_last_data_model()

    partners = Socios.objects.filter(cnpj_empresa=document)\
                             .order_by('nome_socio')
    camara_spending = GastosDeputados.objects.filter(txtcnpjcpf=document)\
                                             .order_by('-datemissao')
    federal_spending = GastosDiretos.objects.filter(codigo_favorecido=document)\
                                    .order_by('-data_pagamento')

    camara_spending_url = reverse(
        'api:dataset-data', kwargs={'slug': 'gastos-deputados'}
    ) + '?txtcnpjcpf=' + str(document)
    federal_spending_url = reverse(
        'api:dataset-data', kwargs={'slug': 'gastos-diretos'}
    ) + '?codigo_favorecido=' + str(document)

    first_partner = partners.first()
    company = {
            'document': document,
            'name': first_partner.nome_empresa,
            'state': first_partner.unidade_federativa,
    }

    context = {
        'company': company,
        'partners': partners,
        'camara_spending': camara_spending,
        'camara_spending_url': camara_spending_url,
        'federal_spending': federal_spending,
        'federal_spending_url': federal_spending_url,
    }
    return render(request, 'specials/company-detail.html', context)
