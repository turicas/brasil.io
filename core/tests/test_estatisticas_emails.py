import datetime

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from mailer.models import PRIORITY_MEDIUM, RESULT_FAILURE, RESULT_SUCCESS, Message, MessageLog, make_message

from core import estatisticas_emails
from traffic_control.tests.util import TrafficControlClient

UTC = datetime.timezone.utc


@pytest.fixture
def client():
    return TrafficControlClient()


INICIO = datetime.datetime(2026, 8, 1, tzinfo=UTC)
FIM = datetime.datetime(2026, 9, 1, tzinfo=UTC)
DIA_10 = datetime.datetime(2026, 8, 10, 15, 0, tzinfo=UTC)
DIA_11 = datetime.datetime(2026, 8, 11, 15, 0, tzinfo=UTC)


def _mensagem(quando=None):
    mensagem = make_message(
        subject="Ativação", body="corpo", from_email="noreply@brasil.io", to=["a@example.com"], priority=PRIORITY_MEDIUM
    )
    mensagem.save()
    if quando is not None:
        Message.objects.filter(pk=mensagem.pk).update(when_added=quando)
        mensagem.refresh_from_db()
    return mensagem


def _tentativa(resultado, enfileirada_em, tentada_em, erro=""):
    """Registra uma tentativa com `when_added` e `when_attempted` exatos e remove a mensagem da fila."""
    mensagem = _mensagem(quando=enfileirada_em)
    MessageLog.objects.log(mensagem, resultado, log_message=erro)
    registro = MessageLog.objects.latest("pk")
    MessageLog.objects.filter(pk=registro.pk).update(when_attempted=tentada_em)
    mensagem.delete()


def _sucesso(tentada_em, atraso):
    _tentativa(RESULT_SUCCESS, enfileirada_em=tentada_em - atraso, tentada_em=tentada_em)


def _falha(tentada_em, erro):
    _tentativa(RESULT_FAILURE, enfileirada_em=tentada_em, tentada_em=tentada_em, erro=erro)


@pytest.mark.django_db
def test_situacao_atual_conta_fila_deferred_e_idade_da_mais_antiga():
    agora = datetime.datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
    _mensagem(quando=agora - datetime.timedelta(minutes=10))
    _mensagem(quando=agora - datetime.timedelta(minutes=2))
    _mensagem(quando=agora - datetime.timedelta(hours=5)).defer()

    situacao = estatisticas_emails.situacao_atual(agora=agora)

    assert situacao.na_fila == 2
    assert situacao.deferred == 1
    assert situacao.idade_mais_antiga == datetime.timedelta(minutes=10)


@pytest.mark.django_db
def test_situacao_atual_sem_fila():
    situacao = estatisticas_emails.situacao_atual()

    assert (situacao.na_fila, situacao.deferred, situacao.idade_mais_antiga) == (0, 0, None)


@pytest.mark.django_db
def test_latencia_por_dia_percentis_e_maximo_com_valores_conhecidos():
    # Três envios no mesmo dia com atrasos de 10s, 60s e 3600s:
    # p50 = 60 (valor do meio); p90 interpola entre 60 e 3600 na posição 1.8 -> 60 + 0.8 * 3540 = 2892
    _sucesso(DIA_10, datetime.timedelta(seconds=10))
    _sucesso(DIA_10, datetime.timedelta(seconds=60))
    _sucesso(DIA_10, datetime.timedelta(seconds=3600))

    [linha] = estatisticas_emails.latencia_por_dia(INICIO, FIM, dias_expiracao=7)

    assert linha.dia == datetime.date(2026, 8, 10)
    assert linha.envios == 3
    assert linha.p50 == datetime.timedelta(seconds=60)
    assert linha.p90 == datetime.timedelta(seconds=2892)
    assert linha.maximo == datetime.timedelta(seconds=3600)
    assert linha.expirados == 0


@pytest.mark.django_db
def test_latencia_conta_envios_apos_expiracao_do_link():
    _sucesso(DIA_10, datetime.timedelta(days=8))
    _sucesso(DIA_10, datetime.timedelta(days=6))

    [linha] = estatisticas_emails.latencia_por_dia(INICIO, FIM, dias_expiracao=7)
    total = estatisticas_emails.latencia_total(INICIO, FIM, dias_expiracao=7)

    assert linha.expirados == 1
    assert total.expirados == 1
    assert total.envios == 2
    assert total.maximo == datetime.timedelta(days=8)


@pytest.mark.django_db
def test_latencia_ignora_falhas_e_fora_do_periodo():
    _sucesso(DIA_10, datetime.timedelta(seconds=5))
    _falha(DIA_10, "Connection refused")
    _sucesso(FIM + datetime.timedelta(days=1), datetime.timedelta(seconds=999))

    total = estatisticas_emails.latencia_total(INICIO, FIM, dias_expiracao=7)

    assert total.envios == 1
    assert total.maximo == datetime.timedelta(seconds=5)


@pytest.mark.django_db
def test_latencia_total_vazia():
    total = estatisticas_emails.latencia_total(INICIO, FIM, dias_expiracao=7)

    assert total.envios == 0
    assert total.p50 is None
    assert total.maximo is None


@pytest.mark.django_db
def test_tentativas_por_dia_separa_sucessos_falhas_e_taxa():
    _sucesso(DIA_10, datetime.timedelta(seconds=1))
    _falha(DIA_10, "Connection refused")
    _falha(DIA_10, "Connection refused")
    _falha(DIA_10, "timed out")
    _sucesso(DIA_11, datetime.timedelta(seconds=1))

    dia_10, dia_11 = estatisticas_emails.tentativas_por_dia(INICIO, FIM)

    assert (dia_10.dia, dia_10.sucessos, dia_10.falhas, dia_10.taxa_falha) == (datetime.date(2026, 8, 10), 1, 3, 0.75)
    assert (dia_11.dia, dia_11.sucessos, dia_11.falhas, dia_11.taxa_falha) == (datetime.date(2026, 8, 11), 1, 0, 0.0)


@pytest.mark.django_db
def test_erros_agrupados_por_mensagem_mais_frequente_primeiro():
    _falha(DIA_10, "timed out")
    _falha(DIA_10, "Connection refused")
    _falha(DIA_11, "Connection refused")

    erros = estatisticas_emails.erros_no_periodo(INICIO, FIM)

    assert [(erro.mensagem, erro.ocorrencias) for erro in erros] == [("Connection refused", 2), ("timed out", 1)]


@pytest.mark.django_db
def test_pagina_exige_staff(client):
    url = reverse("admin:mailer-estatisticas")

    response = client.get(url)

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]


@pytest.mark.django_db
def test_pagina_mostra_numeros(client):
    staff = get_user_model().objects.create_user("staff", "staff@example.com", "senha", is_staff=True)
    client.force_login(staff)
    agora = datetime.datetime.now(tz=UTC)
    _sucesso(agora - datetime.timedelta(hours=1), datetime.timedelta(seconds=45))
    _falha(agora - datetime.timedelta(hours=1), "Connection refused")

    response = client.get(reverse("admin:mailer-estatisticas"), {"dias": 7})

    assert response.status_code == 200
    conteudo = response.content.decode()
    assert "Connection refused" in conteudo
    assert "45s" in conteudo
    assert response.context["dias"] == 7


@pytest.mark.django_db
def test_pagina_ignora_periodo_invalido(client):
    staff = get_user_model().objects.create_user("staff", "staff@example.com", "senha", is_staff=True)
    client.force_login(staff)

    response = client.get(reverse("admin:mailer-estatisticas"), {"dias": "abc"})

    assert response.status_code == 200
    assert response.context["dias"] == 30


@pytest.mark.django_db
def test_changelist_de_messagelog_tem_link_para_estatisticas(client):
    staff = get_user_model().objects.create_superuser("root", "root@example.com", "senha")
    client.force_login(staff)

    response = client.get(reverse("admin:mailer_messagelog_changelist"))

    assert response.status_code == 200
    assert reverse("admin:mailer-estatisticas") in response.content.decode()
