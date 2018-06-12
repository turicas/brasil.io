from unicodedata import normalize

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.forms import TracePathForm
from core.models import Dataset
from graphs.serializers import PathSerializer


cipher_suite = Fernet(settings.FERNET_KEY)


def get_datasets():
    slugs = ['documentos-brasil', 'eleicoes-brasil', 'empresas-socias',
             'filiados-partidos', 'gastos-deputados', 'gastos-diretos',
             'socios-brasil']
    return {slug: Dataset.objects.get(slug=slug) for slug in slugs}


def index(request):
    return render(request, 'specials/index.html', {})


def _get_fields(dataset, remove):
    return [field
            for field in dataset.field_set.all()
            if field.show_on_frontend and field.name not in remove]

def unaccent(text):
    return normalize('NFKD', text).encode('ascii', errors='ignore')\
                                  .decode('ascii')


def document_detail(request, document):
    datasets = get_datasets()
    Candidatos = datasets['eleicoes-brasil'].get_last_data_model()
    Documents = datasets['documentos-brasil'].get_last_data_model()
    EmpresasSocias = datasets['empresas-socias'].get_last_data_model()
    FiliadosPartidos = datasets['filiados-partidos'].get_last_data_model()
    GastosDeputados = datasets['gastos-deputados'].get_last_data_model()
    GastosDiretos = datasets['gastos-diretos'].get_last_data_model()
    Socios = datasets['socios-brasil'].get_last_data_model()

    encrypted = False
    if len(document) not in (11, 14):  # encrypted
        try:
            encrypted_document = document.encode('ascii')
            document_bytes = cipher_suite.decrypt(encrypted_document)
            document = document_bytes.decode('ascii')
            encrypted = True
        except (UnicodeEncodeError, InvalidToken, UnicodeDecodeError):
            raise Http404
    document = document.replace('.', '').replace('-', '').replace('/', '').strip()
    obj = get_object_or_404(Documents, document=document)
    obj_dict = obj.__dict__

    partners_data = Socios.objects.none()
    companies_data = Socios.objects.none()
    applications_data = Candidatos.objects.none()
    filiations_data = FiliadosPartidos.objects.none()
    applications_fields = _get_fields(
        datasets['eleicoes-brasil'],
        remove=['cpf_candidato', 'nome_candidato']
    )
    companies_fields = _get_fields(
        datasets['socios-brasil'],
        remove=['cpf_cnpj_socio', 'nome_socio'],
    )
    camara_spending_fields = _get_fields(
        datasets['gastos-deputados'],
        remove=['txtcnpjcpf', 'txtfornecedor'],
    )
    federal_spending_fields = _get_fields(
        datasets['gastos-diretos'],
        remove=['codigo_favorecido', 'nome_favorecido'],
    )
    partners_fields = _get_fields(
        datasets['socios-brasil'],
        remove=['cnpj_empresa', 'nome_empresa'],
    )
    filiations_fields = _get_fields(
        datasets['filiados-partidos'],
        remove=[],
    )
    # TODO: will fail when selecting by table
    if obj.document_type == 'CNPJ':
        partners_data = \
            Socios.objects.filter(cnpj_empresa=obj.document)\
                          .order_by('nome_socio')
        partner = partners_data.first()
        obj_dict['state'] = partner.unidade_federativa if partner else None
        companies_data = \
            EmpresasSocias.objects.filter(cnpj_socia=obj.document)\
                                  .order_by('nome_empresa')
        companies_fields = _get_fields(
            datasets['empresas-socias'],
            remove=['cnpj_socia'],
        )
    elif obj.document_type == 'CPF':
        companies_data = \
            Socios.objects.filter(nome_socio=unaccent(obj.name))\
                          .distinct('cnpj_empresa', 'nome_empresa')\
                          .order_by('nome_empresa')
        applications_data = \
            Candidatos.objects.filter(cpf_candidato=obj.document)
        filiations_data = \
            FiliadosPartidos.objects.filter(nome_do_filiado=unaccent(obj.name))

    camara_spending_data = \
        GastosDeputados.objects.filter(txtcnpjcpf=obj.document)\
                               .order_by('-datemissao')
    federal_spending_data = \
        GastosDiretos.objects.filter(codigo_favorecido=obj.document)\
                             .order_by('-data_pagamento')

    context = {
        'applications_data': applications_data,
        'applications_fields': applications_fields,
        'camara_spending_data': camara_spending_data,
        'camara_spending_fields': camara_spending_fields,
        'companies_data': companies_data,
        'companies_fields': companies_fields,
        'encrypted': encrypted,
        'federal_spending_data': federal_spending_data,
        'federal_spending_fields': federal_spending_fields,
        'filiations_data': filiations_data,
        'filiations_fields': filiations_fields,
        'obj': obj_dict,
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
