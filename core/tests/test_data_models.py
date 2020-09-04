from django.db import connection

from core.data_models import Substring
from core.models import Table


def test_Substring_expression():
    query = Table.objects.annotate(prefix=Substring("cnpj", 1, 8)).filter(prefix="abcdefgh").query
    sql, args = query.as_sql(query.compiler, connection)
    assert 'Substring("cnpj", 1, 8) = %s' in sql
    assert "abcdefgh" == args[-1]
