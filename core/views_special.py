from unicodedata import normalize

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.forms import CompanyGroupsForm, TracePathForm
from core.models import get_table, get_table_model
from graphs.serializers import CNPJCompanyGroupsSerializer, PathSerializer

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
    Empresa = get_table_model("socios-brasil", "empresa")
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
        companies_data = (
            Socio.objects.filter(nome_socio=unaccent(obj.name))
            .distinct("cnpj", "razao_social")
            .order_by("razao_social")
        )
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


def _get_path(origin, destination):
    types = {"pessoa-juridica": 1, "pessoa-fisica": 2}
    identifiers = {
        "pessoa-juridica": lambda document: str(document or "")[:8],
        "pessoa-fisica": lambda document: document,
    }
    serializer = PathSerializer(
        data={
            "tipo1": types[origin[0]],
            "identificador1": identifiers[origin[0]](origin[1]),
            "tipo2": types[destination[0]],
            "identificador2": identifiers[destination[0]](destination[1]),
            "all_shortest_paths": False,
        }
    )
    serializer.is_valid()
    path = serializer.data["path"]
    return {"nodes": path["nodes"], "links": path["links"]}


def fix_nodes(nodes):
    """Add `cnpj` to company nodes"""

    Documents = get_table_model("documentos-brasil", "documents")

    result = []
    for node in nodes:
        node = node.copy()
        cnpj_root = node.get("cnpj_root")
        if cnpj_root:
            documents = Documents.objects.filter(document_type="CNPJ", docroot=cnpj_root).order_by("document")
            if documents:
                cnpj = documents.first().document
            else:
                cnpj = f"{cnpj_root}000100"

            node["cnpj"] = cnpj
        result.append(node)
    return result


def trace_path(request):
    form = TracePathForm(request.GET or None)
    errors, path, origin_name, destination_name = None, None, None, None

    if form.is_valid():
        origin_name = form.cleaned_data["origin_name"]
        destination_name = form.cleaned_data["destination_name"]
        path = _get_path(
            (form.cleaned_data["origin_type"], form.cleaned_data["origin_identifier"]),
            (form.cleaned_data["destination_type"], form.cleaned_data["destination_identifier"],),
        )

    context = {
        "destination_name": destination_name,
        "errors": errors,
        "form": form,
        "origin_name": origin_name,
        "nodes": fix_nodes(path["nodes"] if path else []),
        "links": path["links"] if path else [],
    }
    return render(request, "specials/trace-path.html", context)


def _get_groups(company):
    data = {"identificador": company.cnpj}
    serializer = CNPJCompanyGroupsSerializer(data=data)
    serializer.is_valid()
    network = serializer.data["network"]
    return {"nodes": network["nodes"], "links": network["links"]}


def company_groups(request):
    form = CompanyGroupsForm(request.GET or None)
    company, nodes, links = None, [], []

    if form.is_valid():
        company = form.cleaned_data["company"]
        groups = _get_groups(company)
        nodes = groups["nodes"]
        links = groups["links"]

    context = {"form": form, "company": company, "nodes": nodes, "links": links}
    return render(request, "specials/company-groups.html", context)
