import re

from django.db import models
from django.db.models.expressions import Expression

from core.models import DatasetTableModelQuerySet, DynamicTableConfig

REGEXP_NOT_FIELD_NAME = re.compile(".*[^a-zA-Z0-9_].*")


class Substring(Expression):
    """Substring SQL function based on Django Expression (SQL with no parameters)"""

    output_field = models.TextField()

    def __init__(self, field_name, pos, length=None, **extra):
        if not isinstance(pos, int) or (length is not None and not isinstance(length, int)):
            raise ValueError("'pos' and 'length' must be integers")
        elif REGEXP_NOT_FIELD_NAME.match(field_name):
            raise ValueError("Invalid value for 'field_name': {}".format(repr(field_name)))

        self.field_name = field_name
        self.pos = pos
        self.length = length

    def __repr__(self):
        if self.length is not None:
            return 'Substring("{}", {}, {})'.format(self.field_name, self.pos, self.length)
        else:
            return 'Substring("{}", {})'.format(self.field_name, self.pos)

    def as_sql(self, compiler, connection):
        return repr(self), []


class SociosBrasilEmpresaMixin:
    @property
    def is_headquarter(self):
        return self.cnpj[:12].endswith("0001")


class SociosBrasilEmpresaQuerySet(DatasetTableModelQuerySet):
    def branches(self, document):
        """Filtra empresas pelos 8 primeiros dígitos do CNPJ (inclui matriz e filiais)"""

        prefix = document[:8]
        return self.annotate(docroot=Substring("cnpj", 1, 8)).filter(docroot=prefix)

    def get_headquarter_or_branch(self, document):
        branches = self.branches(document)

        if not branches.exists():
            # no document found with this prefix - we don't know this company
            raise self.model.DoesNotExist()

        try:
            obj = branches.get(cnpj=document)
        except self.model.DoesNotExist:
            # document not found, but a branch or HQ exists
            obj = None
            for company in branches:
                if company.is_headquarter:
                    obj = company
                    break
            if obj is None:  # There's no HQ, but a branch exists
                obj = branches[0]

        else:
            # document found - let's check if there's a HQ
            if not obj.is_headquarter:
                for company in branches:
                    if company.is_headquarter:
                        obj = company
                        break

        return obj


class EmpresaTableConfig(DynamicTableConfig):
    dataset_slug = "socios-brasil"
    table_name = "empresa"

    def get_model_mixins(self):
        return [SociosBrasilEmpresaMixin]

    def get_model_managers(self):
        return {"objects": SociosBrasilEmpresaQuerySet.as_manager()}
