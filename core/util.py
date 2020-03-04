import csv
import gc
import json
import gzip
import io
import lzma
from textwrap import dedent
from functools import lru_cache
from urllib.request import urlopen, URLError
import socket

import django.db.models.fields
from django.db import connection, reset_queries, transaction
from django.db.utils import ProgrammingError
from rows.plugins.utils import ipartition
from core.models import Table


def create_object(Model, data):
    special_fields = (
        django.db.models.fields.DateField,
        django.db.models.fields.DateTimeField,
        django.db.models.fields.DecimalField,
    )

    for field in Model._meta.fields:
        if (
            isinstance(field, special_fields)
            and not (data.get(field.name) or "").strip()
        ):
            data[field.name] = None

    return Model(**data)


def get_company_by_document(document):
    Documents = (
        Table.objects.for_dataset("documentos-brasil").named("documents").get_model()
    )
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


@lru_cache()
def github_repository_contributors(repositories = [], timeout=1):
    result = []
    for username, repository in repositories:
        url = f"https://api.github.com/repos/{username}/{repository}/contributors"
        try:
            response = urlopen(url, timeout=timeout)
        except URLError:
            return result
        except socket.timeout:
            return result
        else:
            contributors = json.loads(response.read())
            for contributor in contributors:
                url = contributor["url"]
                try:
                    response = urlopen(url, timeout=timeout)
                except (URLError, socket.timeout):
                    continue
                result.append(json.loads(response.read()))
            return result
