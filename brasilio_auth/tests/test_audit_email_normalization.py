from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from model_bakery import baker

User = get_user_model()


def _executar(*args):
    out = StringIO()
    call_command("audit_email_normalization", *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
class TestAuditEmailNormalization:
    def test_lista_usuario_com_email_que_mudaria(self):
        user = baker.make(User, username="alice", email="foo+tag@gmail.com", is_active=True)
        saida = _executar()
        assert f"id={user.id}" in saida
        assert "'foo+tag@gmail.com'" in saida
        assert "'foo@gmail.com'" in saida
        assert "Total de e-mails que mudariam sob normalização: 1" in saida

    def test_lista_usuario_com_email_que_nao_mudaria_quando_default(self):
        user = baker.make(User, username="alice", email="alice@example.com", is_active=True)
        saida = _executar()
        assert f"id={user.id}" in saida
        assert "Total de e-mails que mudariam sob normalização: 0" in saida

    def test_marca_duplicatas_quando_dois_usuarios_normalizam_pro_mesmo_valor(self):
        baker.make(User, username="alice1", email="foo@gmail.com", is_active=True)
        baker.make(User, username="alice2", email="f.o.o@gmail.com", is_active=True)
        saida = _executar()
        assert saida.count("DUPLICATE") == 2

    def test_only_duplicates_filtra_casos_unicos(self):
        baker.make(User, username="solitario", email="alice@example.com", is_active=True)
        baker.make(User, username="bob1", email="bob@gmail.com", is_active=True)
        baker.make(User, username="bob2", email="b.o.b@gmail.com", is_active=True)
        saida = _executar("--only-duplicates")
        assert "solitario" not in saida
        assert "bob1" in saida
        assert "bob2" in saida

    def test_include_inactive_inclui_usuarios_desativados(self):
        baker.make(User, username="user_ativo", email="ativo@example.com", is_active=True)
        baker.make(User, username="user_inativo", email="inativo@example.com", is_active=False)
        saida = _executar("--include-inactive")
        assert "user_ativo" in saida
        assert "user_inativo" in saida

    def test_default_ignora_usuarios_desativados(self):
        baker.make(User, username="user_ativo", email="ativo@example.com", is_active=True)
        baker.make(User, username="user_inativo", email="inativo@example.com", is_active=False)
        saida = _executar()
        assert "user_ativo" in saida
        assert "user_inativo" not in saida

    def test_contadores_finais_estao_corretos(self):
        baker.make(User, username="muda", email="muda+tag@gmail.com", is_active=True)
        baker.make(User, username="dup1", email="dup@gmail.com", is_active=True)
        baker.make(User, username="dup2", email="d.u.p@gmail.com", is_active=True)
        baker.make(User, username="igual", email="igual@example.com", is_active=True)
        saida = _executar()
        assert "Total de e-mails que mudariam sob normalização: 2" in saida
        assert "Total de usuários envolvidos em colisões: 2" in saida
