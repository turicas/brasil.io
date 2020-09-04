from django.db import models
from django.db.models.functions import Substr


class SociosBrasilEmpresaMixin:
    @property
    def is_headquarter(self):
        return self.cnpj[:12].endswith("0001")


class SociosBrasilEmpresaQuerySet(models.QuerySet):
    def branches(self, document):
        """Filtra empresas pelos 8 primeiros dígitos do CNPJ (inclui matriz e filiais)"""

        prefix = document[:8]
        return self.annotate(docroot=Substr("cnpj", 1, 8)).filter(docroot=prefix)

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
