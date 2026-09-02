import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from model_bakery import baker

from brasilio_auth.forms import AdminUserChangeForm, AdminUserCreationForm
from brasilio_auth.tests.utils import criar_conta_legada
from brasilio_auth.unicidade import email_em_colisao, username_em_colisao

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestFuncoesDeColisao:
    def test_username_ignora_maiusculas(self):
        baker.make(User, username="larraw")
        assert username_em_colisao("LARRAW")
        assert not username_em_colisao("outro")

    def test_username_exclui_a_propria_conta(self):
        user = baker.make(User, username="larraw")
        assert not username_em_colisao("Larraw", excluir_id=user.pk)

    def test_email_compara_pelo_normalizado(self):
        baker.make(User, email="user@gmail.com")
        assert email_em_colisao("U.S.E.R+tag@gmail.com")
        assert not email_em_colisao("other@gmail.com")

    def test_email_compara_pelo_texto_exato_para_conta_legada_sem_normalized_email(self):
        criar_conta_legada(email="legado@example.com")
        assert email_em_colisao("LEGADO@example.com")

    def test_email_vazio_nunca_colide(self):
        baker.make(User, email="")
        assert not email_em_colisao("")


class TestGuardaNoSave:
    def test_criar_com_username_que_difere_so_em_maiusculas_falha(self):
        baker.make(User, username="larraw")
        with pytest.raises(ValidationError) as erro:
            User.objects.create_user("Larraw", "b@example.com", "x")
        assert "username" in erro.value.message_dict
        assert 1 == User.objects.filter(username__iexact="larraw").count()

    def test_criar_com_alias_de_email_existente_falha(self):
        baker.make(User, email="user@gmail.com")
        with pytest.raises(ValidationError) as erro:
            User.objects.create_user("outro", "u.ser+x@gmail.com", "x")
        assert "email" in erro.value.message_dict

    def test_trocar_email_para_um_em_uso_falha(self):
        baker.make(User, email="ocupado@example.com")
        user = baker.make(User, email="livre@example.com")
        user.email = "OCUPADO@example.com"
        with pytest.raises(ValidationError):
            user.save()

    def test_trocar_username_para_um_em_uso_falha_mesmo_com_update_fields(self):
        baker.make(User, username="ocupado")
        user = baker.make(User, username="livre")
        user.username = "Ocupado"
        with pytest.raises(ValidationError):
            user.save(update_fields=["username"])

    def test_conta_legada_em_colisao_pode_ser_salva_sem_mudar_username_ou_email(self):
        baker.make(User, email="dup@example.com")
        legada = criar_conta_legada(email="dup@example.com")
        legada.first_name = "Fulana"
        legada.is_active = False
        legada.save()
        legada.refresh_from_db()
        assert "Fulana" == legada.first_name
        assert legada.is_active is False

    def test_salvar_a_propria_conta_sem_mudanca_nao_falha(self):
        user = baker.make(User, username="mesmo", email="mesmo@example.com")
        user.save()

    def test_save_sem_tocar_campos_unicos_nao_faz_query_extra(self):
        baker.make(User, username="x", email="x@example.com")
        user = User.objects.get(username="x")
        with CaptureQueriesContext(connection) as queries:
            user.save(update_fields=["last_login"])
        assert 1 == len(queries)


class TestFormsDoAdmin:
    def test_criacao_rejeita_username_que_difere_so_em_maiusculas(self):
        baker.make(User, username="larraw")
        form = AdminUserCreationForm(
            data={"username": "Larraw", "password1": "senha-forte-123", "password2": "senha-forte-123"}
        )
        assert not form.is_valid()
        assert "username" in form.errors

    def test_edicao_rejeita_email_alias_de_outra_conta(self):
        baker.make(User, email="user@gmail.com")
        user = baker.make(User, username="editada", email="editada@example.com")
        form = AdminUserChangeForm(
            instance=user,
            data={"username": "editada", "email": "u.ser@gmail.com", "date_joined": "2020-01-01 00:00:00"},
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_edicao_aceita_manter_os_proprios_valores(self):
        user = baker.make(User, username="editada", email="editada@example.com")
        form = AdminUserChangeForm(
            instance=user,
            data={"username": "editada", "email": "editada@example.com", "date_joined": "2020-01-01 00:00:00"},
        )
        assert form.is_valid(), form.errors
