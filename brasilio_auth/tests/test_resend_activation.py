import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from model_bakery import baker

from brasilio_auth.models import ActivationResend
from brasilio_auth.services import resend_activation_emails, users_pending_activation_resend

INICIO = datetime.datetime(2025, 11, 7, tzinfo=datetime.timezone.utc)
FIM = datetime.datetime(2026, 3, 17, tzinfo=datetime.timezone.utc)
HOST = "brasil.io"


def _usuario(dias_apos_inicio=10, **kwargs):
    campos = {"is_active": False, "email": "pessoa@example.com"}
    campos.update(kwargs)
    user = baker.make(get_user_model(), **campos)
    get_user_model().objects.filter(pk=user.pk).update(date_joined=INICIO + datetime.timedelta(days=dias_apos_inicio))
    user.refresh_from_db()
    return user


@pytest.mark.django_db
def test_pendentes_sao_inativos_do_periodo_sem_reenvio_e_com_email():
    dentro = _usuario(10, username="dentro")
    _usuario(10, username="ativo", is_active=True)
    _usuario(-1, username="antes")
    _usuario(200, username="depois")
    _usuario(10, username="sem_email", email="")
    ja_reenviado = _usuario(10, username="reenviado")
    ActivationResend.objects.create(user=ja_reenviado)

    assert list(users_pending_activation_resend(INICIO, FIM)) == [dentro]


@pytest.mark.django_db
def test_pendentes_ordenados_do_mais_antigo_ao_mais_novo():
    novo = _usuario(30, username="novo")
    antigo = _usuario(1, username="antigo")

    assert list(users_pending_activation_resend(INICIO, FIM)) == [antigo, novo]


@pytest.mark.django_db
def test_reenvio_manda_email_com_link_e_registra():
    user = _usuario(10, username="fulano")

    enviados = resend_activation_emails(INICIO, FIM, limit=10, host=HOST)

    assert enviados == [user]
    assert ActivationResend.objects.filter(user=user).exists()
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == [user.email]
    assert "Novo link para ativar" in email.subject
    assert f"https://{HOST}/" in email.body
    assert "expirou" in email.body


@pytest.mark.django_db
def test_reenvio_respeita_limite_e_segunda_execucao_continua_de_onde_parou():
    for indice in range(5):
        _usuario(indice, username=f"user{indice}", email=f"user{indice}@example.com")

    primeira = resend_activation_emails(INICIO, FIM, limit=2, host=HOST)
    segunda = resend_activation_emails(INICIO, FIM, limit=2, host=HOST)

    assert [user.username for user in primeira] == ["user0", "user1"]
    assert [user.username for user in segunda] == ["user2", "user3"]
    assert len(mail.outbox) == 4
    assert ActivationResend.objects.count() == 4


@pytest.mark.django_db
def test_usuario_nao_recebe_dois_reenvios():
    _usuario(10, username="fulano")

    resend_activation_emails(INICIO, FIM, limit=10, host=HOST)
    resend_activation_emails(INICIO, FIM, limit=10, host=HOST)

    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_dry_run_lista_sem_enviar_nem_registrar():
    user = _usuario(10, username="fulano")

    enviados = resend_activation_emails(INICIO, FIM, limit=10, host=HOST, dry_run=True)

    assert enviados == [user]
    assert len(mail.outbox) == 0
    assert not ActivationResend.objects.exists()


@pytest.mark.django_db
def test_comando_imprime_resumo(capsys):
    _usuario(10, username="fulano")
    _usuario(11, username="beltrano", email="beltrano@example.com")

    call_command("resend_activation_emails", "--joined-after=2025-11-07", "--joined-before=2026-03-17", "--limit=1")

    saida = capsys.readouterr().out
    assert "fulano" in saida
    assert "Enviados: 1 de 2 pendentes; restam 1" in saida
    assert len(mail.outbox) == 1
