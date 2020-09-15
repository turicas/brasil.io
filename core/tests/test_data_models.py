import pytest
from django.db import connection
from model_bakery import baker

from core.data_models import EmpresaTableConfig, SociosBrasilEmpresaMixin, Substring
from core.models import Table
from core.tests.utils import BaseTestCaseWithSampleDataset


def test_Substring_expression():
    query = Table.objects.annotate(prefix=Substring("cnpj", 1, 8)).filter(prefix="abcdefgh").query
    sql, args = query.as_sql(query.compiler, connection)
    assert 'Substring("cnpj", 1, 8) = %s' in sql
    assert "abcdefgh" == args[-1]


class SociosBrasilEmpresaModelTests(BaseTestCaseWithSampleDataset):
    DATASET_SLUG = "socios-brasil"
    TABLE_NAME = "empresa"
    FIELDS_KWARGS = [
        {"name": "cnpj", "options": {"max_length": 14}, "type": "string", "null": False},
    ]

    def setUp(self):
        self.Empresa = self.TableModel
        self.matriz = baker.make(self.Empresa, cnpj="45536152000141")
        self.filial = baker.make(self.Empresa, cnpj="45536152000841")

    def test_model_is_using_valid_custom_mixin(self):
        # matriz tem suffixo 0001 antes dos dígitos verificadores
        assert isinstance(self.matriz, SociosBrasilEmpresaMixin)
        assert self.matriz.is_headquarter
        # filial não tem suffixo 0001 antes dos dígitos verificadores
        assert isinstance(self.filial, SociosBrasilEmpresaMixin)
        assert not self.filial.is_headquarter

    def test_branches_queryset(self):
        baker.make(self.Empresa)  # other cnpj

        document = "45536152000141"
        docroot = document[:8]
        branches = self.Empresa.objects.branches(document)

        assert 2 == branches.count()
        assert self.matriz in branches
        assert self.filial in branches
        assert docroot == branches[0].docroot
        assert docroot == branches[1].docroot

    def test_get_headquarter_or_branch_custom_query_method(self):
        document = "45536152000141"

        assert self.matriz == self.Empresa.objects.get_headquarter_or_branch(document)
        self.matriz.delete()
        assert self.filial == self.Empresa.objects.get_headquarter_or_branch(document)
        self.filial.delete()
        with pytest.raises(self.Empresa.DoesNotExist):
            self.Empresa.objects.get_headquarter_or_branch(document)


class EmpresaTableConfigTest(BaseTestCaseWithSampleDataset):
    DATASET_SLUG = "socios-brasil"
    TABLE_NAME = "empresa"
    FIELDS_KWARGS = [
        {"name": "cnpj", "options": {"max_length": 14}, "type": "string", "null": False},
    ]

    def test_can_operate_on_top_of_dynamic_model_from_table_config(self):
        assert self.TableModel is EmpresaTableConfig.get_model()
