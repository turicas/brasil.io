from collections import defaultdict
from unicodedata import normalize

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.forms import TracePathForm
from core.models import Dataset
from core.util import get_company_by_document
from graphs.serializers import PathSerializer


cipher_suite = Fernet(settings.FERNET_KEY)


def get_datasets():
    # TODO: we may need to cache these queries
    slugs = (
        'documentos-brasil:documents',
        'eleicoes-brasil:candidatos',
        'eleicoes-brasil:filiados',
        'gastos-deputados:cota_parlamentar',
        'gastos-diretos:gastos',
        'socios-brasil:socios',
        'socios-brasil:empresas',
        'socios-brasil:holdings',
    )
    datasets = defaultdict(dict)
    for slug in slugs:
        dataset_slug, tablename = slug.split(':')
        dataset = Dataset.objects.get(slug=dataset_slug)
        datasets[dataset_slug][tablename] = \
            dataset.get_table(tablename)

    return datasets


def index(request):
    return render(request, 'specials/index.html', {})


def _get_fields(table, remove):
    return [field
            for field in table.field_set.all()
            if field.show_on_frontend and field.name not in remove]

def unaccent(text):
    return normalize('NFKD', text).encode('ascii', errors='ignore')\
                                  .decode('ascii')


def redirect_company(from_document, to_document, warn):
    url = reverse(
        'core:special-document-detail',
        args=[to_document]
    )
    if warn:
        url += "?original_document={}".format(from_document)
    return redirect(url)


def document_detail(request, document):
    datasets = get_datasets()
    Candidatos = datasets['eleicoes-brasil']['candidatos'].get_model()
    Documents = datasets['documentos-brasil']['documents'].get_model()
    Empresas = datasets['socios-brasil']['empresas'].get_model()
    Holdings = datasets['socios-brasil']['holdings'].get_model()
    Socios = datasets['socios-brasil']['socios'].get_model()
    FiliadosPartidos = datasets['eleicoes-brasil']['filiados'].get_model()
    GastosDeputados = datasets['gastos-deputados']['cota_parlamentar'].get_model()
    GastosDiretos = datasets['gastos-diretos']['gastos'].get_model()

    encrypted = False
    if len(document) not in (11, 14):  # encrypted
        try:
            encrypted_document = document.encode('ascii')
            document_bytes = cipher_suite.decrypt(encrypted_document)
            document = document_bytes.decode('ascii')
        except (UnicodeEncodeError, InvalidToken, UnicodeDecodeError):
            raise Http404
        else:
            encrypted = True
    document = document.replace('.', '').replace('-', '').replace('/', '').strip()
    document_size = len(document)
    is_company = document_size == 14
    is_person = document_size == 11

    branches = Documents.objects.none()
    branches_cnpjs = []

    if is_company:
        doc_prefix = document[:8]
        try:
            obj = get_company_by_document(document)
        except Documents.DoesNotExist:
            raise Http404
        # From here only HQs or companies without HQs
        if document != obj.document:
            if obj.document[:12].endswith('0001'):  # HQ
                return redirect_company(document, obj.document, warn=False)
            else:
                return redirect_company(document, obj.document, warn=True)

        branches = Documents.objects.filter(
            docroot=obj.docroot,
            document_type='CNPJ',
        )
        branches_cnpjs = [branch.document for branch in branches]

    else:  # not a company
        doc_prefix = None
        obj = get_object_or_404(Documents, document=document)

    obj_dict = obj.__dict__
    partners_data = Socios.objects.none()
    companies_data = Socios.objects.none()
    applications_data = Candidatos.objects.none()
    filiations_data = FiliadosPartidos.objects.none()
    applications_fields = _get_fields(
        datasets['eleicoes-brasil']['candidatos'],
        remove=['cpf_candidato', 'nome_candidato']
    )
    companies_fields = _get_fields(
        datasets['socios-brasil']['socios'],
        remove=['cpf_cnpj_socio', 'nome_socio'],
    )
    camara_spending_fields = _get_fields(
        datasets['gastos-deputados']['cota_parlamentar'],
        remove=['txtcnpjcpf', 'txtfornecedor'],
    )
    federal_spending_fields = _get_fields(
        datasets['gastos-diretos']['gastos'],
        remove=['codigo_favorecido', 'nome_favorecido'],
    )
    partners_fields = _get_fields(
        datasets['socios-brasil']['socios'],
        remove=['cnpj', 'razao_social'],
    )
    filiations_fields = _get_fields(
        datasets['eleicoes-brasil']['filiados'],
        remove=[],
    )
    branches_fields = _get_fields(
        datasets['documentos-brasil']['documents'],
        remove=['document_type', 'sources', 'text'],
    )

    if is_company:
        partners_data = \
            Socios.objects.filter(cnpj__in=branches_cnpjs)\
                          .order_by('nome_socio')
        company = Empresas.objects.filter(cnpj=obj.document).first()
        obj_dict['state'] = company.uf if company else ''
        companies_data = Holdings.objects.filter(cnpj_socia__in=branches_cnpjs)\
                                         .order_by('razao_social')
        companies_fields = _get_fields(
            datasets['socios-brasil']['holdings'],
            remove=['cnpj_socia'],
        )

        # all appearances of 'obj.document'
        camara_spending_data = \
            GastosDeputados.objects.filter(txtcnpjcpf__in=branches_cnpjs)\
                                   .order_by('-datemissao')
        federal_spending_data = \
            GastosDiretos.objects.filter(codigo_favorecido__in=branches_cnpjs)\
                                 .order_by('-data_pagamento')
    elif is_person:
        companies_data = \
            Socios.objects.filter(nome_socio=unaccent(obj.name))\
                          .distinct('cnpj', 'razao_social')\
                          .order_by('razao_social')
        applications_data = \
            Candidatos.objects.filter(cpf_candidato=obj.document)
        filiations_data = \
            FiliadosPartidos.objects.filter(nome_do_filiado=unaccent(obj.name))

        # all appearances of 'obj.document'
        camara_spending_data = \
            GastosDeputados.objects.filter(txtcnpjcpf=obj.document)\
                                   .order_by('-datemissao')
        federal_spending_data = \
            GastosDiretos.objects.filter(codigo_favorecido=obj.document)\
                                 .order_by('-data_pagamento')

    original_document = request.GET.get('original_document', None)
    context = {
        'applications_data': applications_data,
        'applications_fields': applications_fields,
        'branches': branches,
        'branches_fields': branches_fields,
        'camara_spending_data': camara_spending_data,
        'camara_spending_fields': camara_spending_fields,
        'companies_data': companies_data,
        'companies_fields': companies_fields,
        'doc_prefix': doc_prefix,
        'encrypted': encrypted,
        'federal_spending_data': federal_spending_data,
        'federal_spending_fields': federal_spending_fields,
        'filiations_data': filiations_data,
        'filiations_fields': filiations_fields,
        'obj': obj_dict,
        'original_document': original_document,
        'partners_data': partners_data,
        'partners_fields': partners_fields,
    }
    return render(request, 'specials/document-detail.html', context)


def _get_path(origin, destination):
    serializer = PathSerializer(data={
        'tipo1': origin['type'],
        'identificador1': origin['identifier'],
        'tipo2': destination['type'],
        'identificador2': destination['identifier'],
        'all_shortest_paths': False,
    })
    serializer.is_valid()
    return serializer.data['path']['nodes']


def trace_path(request):
    form = TracePathForm(request.GET or None)
    errors, path, origin_name, destination_name = None, None, None, None

    if form.is_valid():
        origin_name = form.cleaned_data['origin_name']
        destination_name = form.cleaned_data['destination_name']
        path = _get_path(
            {
                'type': 1 if form.cleaned_data['origin_type'] == 'pessoa-juridica' else 2,
                'identifier': form.cleaned_data['origin_identifier'],
            },
            {
                'type': 1 if form.cleaned_data['destination_type'] == 'pessoa-juridica' else 2,
                'identifier': form.cleaned_data['destination_identifier'],
            },
        )

    context = {
        'destination_name': destination_name,
        'errors': errors,
        'form': form,
        'origin_name': origin_name,
        'path': path,
    }
    return render(request, 'specials/trace-path.html', context)
