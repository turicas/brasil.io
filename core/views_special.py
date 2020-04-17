import datetime
import json
from collections import defaultdict
from unicodedata import normalize

from cached_property import cached_property
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.db.models import Max, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from core.forms import TracePathForm, CompanyGroupsForm
from core.models import get_table, get_table_model
from core.util import get_company_by_document
from graphs.serializers import PathSerializer, CNPJCompanyGroupsSerializer


cipher_suite = Fernet(settings.FERNET_KEY)


def index(request):
    return render(request, "specials/index.html", {})


def _get_fields(table, remove):
    return [
        field
        for field in table.field_set.all()
        if field.show_on_frontend and field.name not in remove
    ]


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
    Empresas = get_table_model("socios-brasil", "empresas")
    Holdings = get_table_model("socios-brasil", "holdings")
    Socios = get_table_model("socios-brasil", "socios")
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
            if obj.document[:12].endswith("0001"):  # HQ
                return redirect_company(document, obj.document, warn=False)
            else:
                return redirect_company(document, obj.document, warn=True)

        branches = Documents.objects.filter(docroot=obj.docroot, document_type="CNPJ")
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
        get_table("eleicoes-brasil", "candidatos"),
        remove=["cpf_candidato", "nome_candidato"],
    )
    companies_fields = _get_fields(
        get_table("socios-brasil", "socios"), remove=["cpf_cnpj_socio", "nome_socio"]
    )
    camara_spending_fields = _get_fields(
        get_table("gastos-deputados", "cota_parlamentar"),
        remove=["txtcnpjcpf", "txtfornecedor"],
    )
    federal_spending_fields = _get_fields(
        get_table("gastos-diretos", "gastos"),
        remove=["codigo_favorecido", "nome_favorecido"],
    )
    partners_fields = _get_fields(
        get_table("socios-brasil", "socios"), remove=["cnpj", "razao_social"]
    )
    filiations_fields = _get_fields(get_table("eleicoes-brasil", "filiados"), remove=[])
    branches_fields = _get_fields(
        get_table("documentos-brasil", "documents"),
        remove=["document_type", "sources", "text"],
    )

    if is_company:
        partners_data = Socios.objects.filter(cnpj__in=branches_cnpjs).order_by(
            "nome_socio"
        )
        company = Empresas.objects.filter(cnpj=obj.document).first()
        obj_dict["state"] = company.uf if company else ""
        companies_data = Holdings.objects.filter(
            cnpj_socia__in=branches_cnpjs
        ).order_by("razao_social")
        companies_fields = _get_fields(
            get_table("socios-brasil", "holdings"), remove=["cnpj_socia"]
        )

        # all appearances of 'obj.document'
        camara_spending_data = GastosDeputados.objects.filter(
            txtcnpjcpf__in=branches_cnpjs
        ).order_by("-datemissao")
        federal_spending_data = GastosDiretos.objects.filter(
            codigo_favorecido__in=branches_cnpjs
        ).order_by("-data_pagamento")
    elif is_person:
        companies_data = (
            Socios.objects.filter(nome_socio=unaccent(obj.name))
            .distinct("cnpj", "razao_social")
            .order_by("razao_social")
        )
        applications_data = Candidatos.objects.filter(cpf_candidato=obj.document)
        filiations_data = FiliadosPartidos.objects.filter(
            nome_do_filiado=unaccent(obj.name)
        )

        # all appearances of 'obj.document'
        camara_spending_data = GastosDeputados.objects.filter(
            txtcnpjcpf=obj.document
        ).order_by("-datemissao")
        federal_spending_data = GastosDiretos.objects.filter(
            codigo_favorecido=obj.document
        ).order_by("-data_pagamento")

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
        "encrypted": encrypted,
        "federal_spending_data": federal_spending_data,
        "federal_spending_fields": federal_spending_fields,
        "filiations_data": filiations_data,
        "filiations_fields": filiations_fields,
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
            documents = Documents.objects.filter(
                document_type="CNPJ", docroot=cnpj_root
            ).order_by("document")
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
            (
                form.cleaned_data["destination_type"],
                form.cleaned_data["destination_identifier"],
            ),
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
    data = {"identificador": company.document}
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


class Covid19Stats:

    def __init__(self):
        self.Boletim = get_table_model("covid19", "boletim")
        self.Caso = get_table_model("covid19", "caso")

    @cached_property
    def city_cases(self):
        return self.Caso.objects.filter(is_last=True, place_type="city")

    @cached_property
    def state_cases(self):
        return self.Caso.objects.filter(is_last=True, place_type="state")

    @property
    def total_reports(self):
        return self.Boletim.objects.count()

    @property
    def affected_cities(self):
        return self.city_cases.count()

    @property
    def cities_with_deaths(self):
        return self.city_cases.filter(deaths__gt=0).count()

    @property
    def state_totals(self):
        return self.state_cases.aggregate(
            total_confirmed=Sum("confirmed"),
            total_deaths=Sum("deaths"),
            total_population=Sum("estimated_population_2019"),
        )

    @property
    def total_confirmed(self):
        return self.state_totals["total_confirmed"]

    @property
    def total_deaths(self):
        return self.state_totals["total_deaths"]

    @property
    def total_population(self):
        return self.state_totals["total_population"]

    @property
    def city_totals(self):
        return self.city_cases.aggregate(
            max_confirmed=Max("confirmed"),
            max_confirmed_per_100k_inhabitants=Max("confirmed_per_100k_inhabitants"),
            max_death_rate=Max("death_rate"),
            max_deaths=Max("deaths"),
            total_population=Sum("estimated_population_2019")
        )

    @property
    def affected_population(self):
        return self.city_totals["total_population"]


def covid19(request):
    stats = Covid19Stats()
    affected_cities = stats.affected_cities
    affected_population = stats.affected_population
    cities_with_deaths = stats.cities_with_deaths
    total_confirmed = stats.total_confirmed
    total_deaths = stats.total_deaths
    total_population = stats.total_population

    aggregate = [
        {
            "title": "Boletins coletados",
            "value": stats.total_reports,
            "tooltip": "Total de boletins das Secretarias Estaduais de Saúde coletados pelos voluntários",
        },
        {
            "title": "Casos confirmados",
            "value": total_confirmed,
            "tooltip": "Total de casos confirmados",
        },
        {
            "title": "Óbitos confirmados",
            "value": total_deaths,
            "tooltip": "Total de óbitos confirmados",
        },
        {
            "title": "Municípios atingidos",
            "value": f"{affected_cities} ({100 * affected_cities / 5570:.0f}%)",
            "tooltip": "Total de municípios com casos confirmados",
        },
        {
            "title": "População desses municípios",
            "value": f"{affected_population / 1_000_000:.0f}M ({100 * (affected_population / total_population):.0f}%)",
            "tooltip": "População dos municípios com casos confirmados, segundo estimativa IBGE 2019",
        },
        {
            "title": "Municípios c/ óbitos",
            "value": f"{cities_with_deaths} ({100 * cities_with_deaths / affected_cities:.0f}%)",
            "tooltip": "Total de municípios com óbitos confirmados (o percentual é em relação ao total de municípios com casos confirmados)",
        },
    ]

    value_keys = ("confirmed", "deaths", "death_rate", "confirmed_per_100k_inhabitants")
    city_values = {key: {} for key in value_keys}
    city_data = []
    # TODO: what should we do about "Importados/Indefinidos"?
    for row in stats.city_cases.filter(city_ibge_code__isnull=False):
        row = row.__dict__
        for key in value_keys:
            row[key] = row[key] or 0
            city_values[key][row["city_ibge_code"]] = row[key]
        row["death_rate_percent"] = row.pop("death_rate") * 100
        row["date_str"] = str(row["date"])
        row["city_str"] = slugify(row["city"])
        year, month, day = row["date_str"].split("-")
        row["date"] = datetime.date(int(year), int(month), int(day))
        city_data.append(row)
    max_values = {key: max(city_values[key].values()) for key in value_keys}

    return render(
        request,
        "specials/covid19.html",
        {"city_data": city_data, "aggregate": aggregate, "city_values_json": json.dumps(city_values), "max_values_json": json.dumps(max_values)},
    )
