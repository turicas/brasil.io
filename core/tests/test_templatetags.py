import datetime

import pytest

from core.templatetags.utils import duracao


@pytest.mark.parametrize(
    "valor, esperado",
    [
        (None, "-"),
        (datetime.timedelta(0), "0s"),
        (datetime.timedelta(seconds=12), "12s"),
        (datetime.timedelta(seconds=59.4), "59s"),
        (datetime.timedelta(seconds=60), "1.0min"),
        (datetime.timedelta(seconds=210), "3.5min"),
        (datetime.timedelta(minutes=59, seconds=59), "60.0min"),
        (datetime.timedelta(hours=1), "1.0h"),
        (datetime.timedelta(hours=2, minutes=6), "2.1h"),
        (datetime.timedelta(hours=23, minutes=59), "24.0h"),
        (datetime.timedelta(days=1), "1.0d"),
        (datetime.timedelta(days=128), "128.0d"),
        (90, "1.5min"),
        ("3600", "1.0h"),
    ],
)
def test_duracao_formata_por_escala(valor, esperado):
    assert duracao(valor) == esperado
