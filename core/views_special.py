from unicodedata import normalize

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.data_models import EmpresaTableConfig
from core.models import get_table, get_table_model

cipher_suite = Fernet(settings.FERNET_KEY)


def index(request):
    return render(request, "specials/index.html", {})


def _get_fields(table, remove=None, only=None):
    if only is not None and remove is not None:
        raise ValueError("Cannot have only and remove at the same time")
    elif remove:
        return [field for field in table.field_set.all() if field.show_on_frontend and field.name not in remove]
    elif only:
        return [field for field in table.field_set.all() if field.show_on_frontend and field.name in only]


def unaccent(text):
    return normalize("NFKD", text).encode("ascii", errors="ignore").decode("ascii")


def redirect_company(from_document, to_document, warn):
    url = reverse("core:special-document-detail", args=[to_document])
    if warn:
        url += "?original_document={}".format(from_document)
    return redirect(url)


def document_detail(request, document):
    Candidatos = get_table_model("eleicoes-brasil", "candidatos")
    Documents = get_table_model("documentos-brasil", "documents")
    Empresa = EmpresaTableConfig.get_model()
    Holding = get_table_model("socios-brasil", "holding")
    Socio = get_table_model("socios-brasil", "socio")
    FiliadosPartidos = get_table_model("eleicoes-brasil", "filiados")
    GastosDeputados = get_table_model("gastos-deputados", "cota_parlamentar")
    GastosDiretos = get_table_model("gastos-diretos", "gastos")

    encrypted = False
    if len(document) not in (11, 14):  # encrypted
        try:
            encrypted_document = document.encode("ascii")
            document_bytes = cipher_suite.decrypt(encrypted_document)
            document = document_bytes.decode("ascii")
        except (UnicodeEncodeError, InvalidToken, UnicodeDecodeError):
            raise Http404
        else:
            encrypted = True
    document = document.replace(".", "").replace("-", "").replace("/", "").strip()
    document_size = len(document)
    is_company = document_size == 14
    is_person = document_size == 11

    branches = Empresa.objects.none()
    branches_cnpjs = []

    if is_company:
        try:
            obj = Empresa.objects.get_headquarter_or_branch(document)
        except ObjectDoesNotExist:
            raise Http404
        # From here only HQs or companies without HQs
        if document != obj.cnpj:
            if obj.is_headquarter:
                return redirect_company(document, obj.cnpj, warn=False)
            else:
                return redirect_company(document, obj.cnpj, warn=True)

        doc_prefix = document[:8]
        branches = Empresa.objects.branches(document)
        branches_cnpjs = [company.cnpj for company in branches]

    else:  # not a company
        # TODO: check another way of getting CPFs
        doc_prefix = None
        obj = get_object_or_404(Documents, document=document)

    obj_dict = obj.__dict__
    if is_company:
        obj_dict["document"] = obj.cnpj
        # TODO: add document if is_person after migrating from documentos-brasil
    partners_data = Socio.objects.none()
    companies_data = Socio.objects.none()
    applications_data = Candidatos.objects.none()
    filiations_data = FiliadosPartidos.objects.none()
    applications_fields = _get_fields(
        get_table("eleicoes-brasil", "candidatos", allow_hidden=True), remove=["cpf_candidato", "nome_candidato"],
    )
    companies_fields = _get_fields(
        get_table("socios-brasil", "socio", allow_hidden=True), remove=["cpf_cnpj_socio", "nome_socio"]
    )
    camara_spending_fields = _get_fields(
        get_table("gastos-deputados", "cota_parlamentar", allow_hidden=True), remove=["txtcnpjcpf", "txtfornecedor"],
    )
    federal_spending_fields = _get_fields(
        get_table("gastos-diretos", "gastos", allow_hidden=True), remove=["codigo_favorecido", "nome_favorecido"],
    )
    partners_fields = _get_fields(
        get_table("socios-brasil", "socio", allow_hidden=True), remove=["cnpj", "razao_social"]
    )
    filiations_fields = _get_fields(get_table("eleicoes-brasil", "filiados", allow_hidden=True), remove=[])
    branches_fields = _get_fields(
        get_table("socios-brasil", "empresa", allow_hidden=True), only=["cnpj", "razao_social", "nome_fantasia"],
    )

    if is_company:
        # Cada filial vai ter os mesmos sócios, por isso precisamos do
        # `distinct` nas colunas que serão exibidas na interface.
        partners_data = (
            Socio.objects.filter(cnpj__in=branches_cnpjs)
            .distinct(*[field.name for field in partners_fields])
            .order_by("nome_socio")
        )

        obj_dict["state"] = obj.uf
        obj_dict["name"] = obj.razao_social
        companies_data = Holding.objects.filter(holding_cnpj__in=branches_cnpjs).order_by("holding_razao_social")
        companies_fields = _get_fields(
            get_table("socios-brasil", "holding", allow_hidden=True),
            remove=["holding_cnpj", "holding_razao_social", "codigo_qualificacao_socia"],
        )

        camara_spending_data = GastosDeputados.objects.filter(txtcnpjcpf__in=branches_cnpjs).order_by("-datemissao")
        federal_spending_data = GastosDiretos.objects.filter(codigo_favorecido__in=branches_cnpjs).order_by(
            "-data_pagamento"
        )
    elif is_person:
        companies_data = Socio.objects.filter(nome_socio=unaccent(obj.name)).distinct("cnpj").order_by("cnpj")
        # TODO: filter by CPF also
        applications_data = Candidatos.objects.filter(cpf_candidato=obj.document)
        filiations_data = FiliadosPartidos.objects.filter(nome_do_filiado=unaccent(obj.name))

        # all appearances of 'obj.document'
        camara_spending_data = GastosDeputados.objects.filter(txtcnpjcpf=obj.document).order_by("-datemissao")
        federal_spending_data = GastosDiretos.objects.filter(codigo_favorecido=obj.document).order_by("-data_pagamento")

    original_document = request.GET.get("original_document", None)
    context = {
        "applications_data": applications_data,
        "applications_fields": applications_fields,
        "branches": branches,
        "branches_fields": branches_fields,
        "camara_spending_data": camara_spending_data,
        "camara_spending_fields": camara_spending_fields,
        "companies_data": companies_data,
        "companies_fields": companies_fields,
        "doc_prefix": doc_prefix,
        "document_type": "CNPJ" if is_company else "CPF",
        "encrypted": encrypted,
        "federal_spending_data": federal_spending_data,
        "federal_spending_fields": federal_spending_fields,
        "filiations_data": filiations_data,
        "filiations_fields": filiations_fields,
        "is_company": is_company,
        "is_person": is_person,
        "obj": obj_dict,
        "original_document": original_document,
        "partners_data": partners_data,
        "partners_fields": partners_fields,
    }
    return render(request, "specials/document-detail.html", context)
