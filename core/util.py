import gzip
import json
import socket
from urllib.request import urlopen, Request, URLError

import django.db.models.fields
from cachetools import cached, TTLCache

from core.models import Table


def create_object(Model, data):
    special_fields = (
        django.db.models.fields.DateField,
        django.db.models.fields.DateTimeField,
        django.db.models.fields.DecimalField,
    )

    for field in Model._meta.fields:
        if isinstance(field, special_fields) and not (data.get(field.name) or "").strip():
            data[field.name] = None

    return Model(**data)


def get_company_by_document(document):
    Documents = Table.objects.for_dataset("documentos-brasil").named("documents").get_model()
    doc_prefix = document[:8]
    headquarter_prefix = doc_prefix + "0001"
    branches = Documents.objects.filter(docroot=doc_prefix, document_type="CNPJ")
    if not branches.exists():
        # no document found with this prefix - we don't know this company
        raise Documents.DoesNotExist()

    try:
        obj = branches.get(document=document)
    except Documents.DoesNotExist:
        # document not found, but a branch or HQ exists
        try:
            obj = branches.get(document__startswith=headquarter_prefix)
        except Documents.DoesNotExist:
            # there's no HQ, but a branch exists
            obj = branches[0]

    else:
        # document found - let's check if there's a HQ
        if not document.startswith(headquarter_prefix):
            try:
                obj = branches.get(document__startswith=headquarter_prefix)
            except Documents.DoesNotExist:
                # there's no HQ, but the object was found anyway
                pass

    return obj


def http_get(url, timeout):
    """Execute a HTTP GET request and returns `None` if `timeout` is achieved.

    This function is capable of decompressing data automatically from HTTP
    server."""

    request = Request(url, headers={"Accept-Encoding": "gzip, deflate"})
    try:
        response = urlopen(request, timeout=timeout)
    except (URLError, socket.timeout):
        return None
    else:
        encoding = response.info().get("Content-Encoding")
        response_data = response.read()
        if encoding in ("deflate", None):
            data = response_data
        elif encoding == "gzip":
            data = gzip.decompress(response_data)
        else:
            raise RuntimeError(f"Unknown encoding: {repr(encoding)}")
        return data


def http_get_json(url, timeout):
    data = http_get(url, timeout)
    if data is not None:
        data = json.loads(data)
    return data


@cached(cache=TTLCache(maxsize=100, ttl=24 * 3600))
def cached_http_get_json(url, timeout):
    return http_get_json(url, timeout)


@cached(cache=TTLCache(maxsize=100, ttl=24 * 3600))
def github_repository_contributors(username, repository, timeout=1):
    url = f"https://api.github.com/repos/{username}/{repository}/contributors"
    contributors = cached_http_get_json(url, timeout)
    if contributors is None:
        print(f"ERROR downloading {url}")
        return []

    for contributor in contributors:
        url = contributor["url"]
        contributor["user_data"] = cached_http_get_json(contributor["url"], timeout)
        if contributor["user_data"] is None:
            print(f"ERROR downloading {url}")

    return contributors


def brasilio_github_contributors():
    repositories = (
        ("turicas", "balneabilidade-brasil"),
        ("turicas", "blog.brasil.io"),
        ("turicas", "brasil"),
        ("turicas", "brasil.io"),
        ("turicas", "censo-ibge"),
        ("turicas", "covid19-br"),
        ("turicas", "cursos-prouni"),
        ("turicas", "data-worker"),
        ("turicas", "eleicoes-brasil"),
        ("turicas", "gastos-deputados"),
        ("turicas", "genero-nomes"),
        ("turicas", "portaldatransparencia"),
        ("turicas", "salarios-magistrados"),
        ("turicas", "socios-brasil"),
        ("turicas", "transparencia-gov-br"),
    )
    contributor_data = {}
    for account, repository in repositories:
        contributors = github_repository_contributors(account, repository)
        for contributor in contributors:
            if contributor["user_data"] is None:
                print(f"ERROR getting data for {contributor['login']}")
                continue
            username = contributor["login"]
            if username not in contributor_data:
                contributor_data[username] = contributor["user_data"]
            if "contributions" not in contributor_data[username]:
                contributor_data[username]["contributions"] = 0
            contributor_data[username]["contributions"] += contributor["contributions"]
    total_contributors = list(contributor_data.values())
    total_contributors.sort(key=lambda row: row["contributions"], reverse=True)
    return total_contributors
