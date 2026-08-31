"""Estatísticas de entrega de e-mails (django-mailer) para a página do admin.

Todos os números vêm direto de linhas de `mailer_messagelog` e `mailer_message`, sem agrupar tentativas por mensagem (o
`MessageLog` não referencia a mensagem, então qualquer agrupamento seria heurística).

Percentis via `percentile_cont`: p50 (mediana) é o atraso que metade dos envios não ultrapassa; p90 e p99, o que 90% e
99% não ultrapassam. Interpola entre valores vizinhos.
"""

import datetime
from dataclasses import dataclass

from django.conf import settings
from django.db import connection
from django.utils import timezone
from mailer.models import Message

SQL_TENTATIVAS_POR_DIA = """
SELECT
    date_trunc('day', when_attempted AT TIME ZONE %(fuso)s)::date AS dia,
    count(*) FILTER (WHERE result = '1') AS sucessos,
    count(*) FILTER (WHERE result <> '1') AS falhas
FROM mailer_messagelog
WHERE when_attempted >= %(inicio)s AND when_attempted < %(fim)s
GROUP BY 1
ORDER BY 1
"""

SQL_ERROS = """
SELECT log_message, count(*) AS ocorrencias
FROM mailer_messagelog
WHERE result <> '1' AND when_attempted >= %(inicio)s AND when_attempted < %(fim)s
GROUP BY 1
ORDER BY 2 DESC, 1
"""

SQL_LATENCIA_POR_DIA = """
SELECT
    date_trunc('day', when_attempted AT TIME ZONE %(fuso)s)::date AS dia,
    count(*) AS envios,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (when_attempted - when_added))) AS p50,
    percentile_cont(0.9) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (when_attempted - when_added))) AS p90,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (when_attempted - when_added))) AS p99,
    max(EXTRACT(EPOCH FROM (when_attempted - when_added))) AS maximo,
    count(*) FILTER (WHERE when_attempted - when_added > make_interval(days => %(dias_expiracao)s)) AS expirados
FROM mailer_messagelog
WHERE result = '1' AND when_attempted >= %(inicio)s AND when_attempted < %(fim)s
GROUP BY 1
ORDER BY 1
"""

SQL_LATENCIA_TOTAL = """
SELECT
    count(*) AS envios,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (when_attempted - when_added))) AS p50,
    percentile_cont(0.9) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (when_attempted - when_added))) AS p90,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (when_attempted - when_added))) AS p99,
    max(EXTRACT(EPOCH FROM (when_attempted - when_added))) AS maximo,
    count(*) FILTER (WHERE when_attempted - when_added > make_interval(days => %(dias_expiracao)s)) AS expirados
FROM mailer_messagelog
WHERE result = '1' AND when_attempted >= %(inicio)s AND when_attempted < %(fim)s
"""


@dataclass
class Situacao:
    na_fila: int
    deferred: int
    idade_mais_antiga: datetime.timedelta | None


@dataclass
class TentativasDia:
    dia: datetime.date
    sucessos: int
    falhas: int

    @property
    def taxa_falha(self) -> float:
        total = self.sucessos + self.falhas
        return self.falhas / total if total else 0.0


@dataclass
class Erro:
    mensagem: str
    ocorrencias: int


@dataclass
class Latencia:
    envios: int
    p50: datetime.timedelta | None
    p90: datetime.timedelta | None
    p99: datetime.timedelta | None
    maximo: datetime.timedelta | None
    expirados: int
    dia: datetime.date | None = None


def _segundos(valor) -> datetime.timedelta | None:
    return None if valor is None else datetime.timedelta(seconds=float(valor))


def _consultar(sql, parametros):
    with connection.cursor() as cursor:
        cursor.execute(sql, parametros)
        return cursor.fetchall()


def situacao_atual(agora=None) -> Situacao:
    agora = agora or timezone.now()
    mais_antiga = Message.objects.non_deferred().order_by("when_added").values_list("when_added", flat=True).first()
    return Situacao(
        na_fila=Message.objects.non_deferred().count(),
        deferred=Message.objects.deferred().count(),
        idade_mais_antiga=None if mais_antiga is None else agora - mais_antiga,
    )


def tentativas_por_dia(inicio, fim) -> list[TentativasDia]:
    linhas = _consultar(SQL_TENTATIVAS_POR_DIA, {"inicio": inicio, "fim": fim, "fuso": settings.TIME_ZONE})
    return [TentativasDia(dia=dia, sucessos=sucessos, falhas=falhas) for dia, sucessos, falhas in linhas]


def erros_no_periodo(inicio, fim) -> list[Erro]:
    linhas = _consultar(SQL_ERROS, {"inicio": inicio, "fim": fim})
    return [Erro(mensagem=mensagem, ocorrencias=ocorrencias) for mensagem, ocorrencias in linhas]


def latencia_por_dia(inicio, fim, dias_expiracao=None) -> list[Latencia]:
    dias_expiracao = settings.ACCOUNT_ACTIVATION_DAYS if dias_expiracao is None else dias_expiracao
    parametros = {"inicio": inicio, "fim": fim, "fuso": settings.TIME_ZONE, "dias_expiracao": dias_expiracao}
    return [
        Latencia(
            dia=dia,
            envios=envios,
            p50=_segundos(p50),
            p90=_segundos(p90),
            p99=_segundos(p99),
            maximo=_segundos(maximo),
            expirados=expirados,
        )
        for dia, envios, p50, p90, p99, maximo, expirados in _consultar(SQL_LATENCIA_POR_DIA, parametros)
    ]


def latencia_total(inicio, fim, dias_expiracao=None) -> Latencia:
    dias_expiracao = settings.ACCOUNT_ACTIVATION_DAYS if dias_expiracao is None else dias_expiracao
    parametros = {"inicio": inicio, "fim": fim, "dias_expiracao": dias_expiracao}
    envios, p50, p90, p99, maximo, expirados = _consultar(SQL_LATENCIA_TOTAL, parametros)[0]
    return Latencia(
        envios=envios,
        p50=_segundos(p50),
        p90=_segundos(p90),
        p99=_segundos(p99),
        maximo=_segundos(maximo),
        expirados=expirados,
    )
