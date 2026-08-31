import datetime

import pytest
from django.utils import timezone
from mailer.models import PRIORITY_MEDIUM, RESULT_FAILURE, RESULT_SUCCESS, Message, MessageLog, make_message

from core.entrega_emails import verificar_entrega_emails

JANELA = datetime.timedelta(hours=1)
IDADE_MAXIMA = datetime.timedelta(minutes=15)


def _mensagem(quando=None):
    mensagem = make_message(
        subject="Ativação", body="corpo", from_email="noreply@brasil.io", to=["a@example.com"], priority=PRIORITY_MEDIUM
    )
    mensagem.save()
    if quando is not None:
        Message.objects.filter(pk=mensagem.pk).update(when_added=quando)
        mensagem.refresh_from_db()
    return mensagem


def _tentativa(resultado, erro="", quando=None):
    mensagem = _mensagem()
    MessageLog.objects.log(mensagem, resultado, log_message=erro)
    registro = MessageLog.objects.latest("pk")
    if quando is not None:
        MessageLog.objects.filter(pk=registro.pk).update(when_attempted=quando)
    mensagem.delete()
    return registro


@pytest.mark.django_db
def test_sem_mensagens_e_sem_tentativas_esta_saudavel():
    assert verificar_entrega_emails(JANELA, IDADE_MAXIMA) == []


@pytest.mark.django_db
def test_somente_sucessos_na_janela_esta_saudavel():
    _tentativa(RESULT_SUCCESS)
    assert verificar_entrega_emails(JANELA, IDADE_MAXIMA) == []


@pytest.mark.django_db
def test_falha_na_janela_gera_problema_com_contagens_e_erros():
    _tentativa(RESULT_FAILURE, erro="[Errno 111] Connection refused")
    _tentativa(RESULT_FAILURE, erro="[Errno 111] Connection refused")
    _tentativa(RESULT_SUCCESS)

    problemas = verificar_entrega_emails(JANELA, IDADE_MAXIMA)

    assert [problema.tipo for problema in problemas] == ["falhas"]
    assert problemas[0].detalhes["falhas"] == 2
    assert problemas[0].detalhes["sucessos"] == 1
    assert problemas[0].detalhes["erros"] == ["[Errno 111] Connection refused"]
    assert "2 falha(s)" in problemas[0].mensagem


@pytest.mark.django_db
def test_falha_fora_da_janela_e_ignorada():
    antes = timezone.now() - JANELA - datetime.timedelta(minutes=1)
    _tentativa(RESULT_FAILURE, erro="timeout", quando=antes)
    assert verificar_entrega_emails(JANELA, IDADE_MAXIMA) == []


@pytest.mark.django_db
def test_mensagem_deferred_gera_problema():
    mensagem = _mensagem()
    mensagem.defer()

    problemas = verificar_entrega_emails(JANELA, IDADE_MAXIMA)

    assert [problema.tipo for problema in problemas] == ["deferred"]
    assert problemas[0].detalhes["deferred"] == 1


@pytest.mark.django_db
def test_mensagem_recente_na_fila_nao_e_problema():
    _mensagem()
    assert verificar_entrega_emails(JANELA, IDADE_MAXIMA) == []


@pytest.mark.django_db
def test_mensagem_antiga_na_fila_indica_fila_parada():
    _mensagem(quando=timezone.now() - IDADE_MAXIMA - datetime.timedelta(minutes=1))

    problemas = verificar_entrega_emails(JANELA, IDADE_MAXIMA)

    assert [problema.tipo for problema in problemas] == ["fila_parada"]
    assert problemas[0].detalhes["na_fila"] == 1


@pytest.mark.django_db
def test_mensagem_deferred_antiga_nao_conta_como_fila_parada():
    mensagem = _mensagem(quando=timezone.now() - datetime.timedelta(hours=2))
    mensagem.defer()

    problemas = verificar_entrega_emails(JANELA, IDADE_MAXIMA)

    assert [problema.tipo for problema in problemas] == ["deferred"]
