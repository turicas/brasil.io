from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.models import Dataset


cipher_suite = Fernet(settings.FERNET_KEY)

def index(request):
    return render(request, 'specials/index.html', {})


def document_detail(request, document):
    Documents = Dataset.objects.get(slug='documentos-brasil').get_last_data_model()
    Socios = Dataset.objects.get(slug='socios-brasil').get_last_data_model()
    GastosDeputados = Dataset.objects.get(slug='gastos-deputados').get_last_data_model()
    GastosDiretos = Dataset.objects.get(slug='gastos-diretos').get_last_data_model()

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

    partners, companies = None, None
    if obj.document_type == 'cnpj':
        partners = Socios.objects.filter(cnpj_empresa=obj.document)\
                                 .order_by('nome_socio')
    elif obj.document_type == 'cpf':
        companies = Socios.objects.filter(nome_socio=obj.name)\
                                  .values('cnpj_empresa', 'nome_empresa')\
                                  .distinct()\
                                  .order_by('nome_empresa')

    camara_spending = GastosDeputados.objects.filter(txtcnpjcpf=obj.document)\
                                             .order_by('-datemissao')
    federal_spending = GastosDiretos.objects.filter(codigo_favorecido=obj.document)\
                                    .order_by('-data_pagamento')

    obj = obj.__dict__
    if partners:
        partner = partners.first()
        obj['state'] = partner.unidade_federativa if partner else None

    context = {
        'camara_spending': camara_spending,
        'companies': companies,
        'encrypted': encrypted,
        'federal_spending': federal_spending,
        'obj': obj,
        'partners': partners,
    }
    return render(request, 'specials/document-detail.html', context)
