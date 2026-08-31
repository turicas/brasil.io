from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from model_bakery import baker

from brasilio_auth.models import NormalizedEmail
from brasilio_auth.tests.utils import criar_conta_legada

User = get_user_model()


class SyncNormalizedEmailSignalTests(TestCase):
    def test_sinal_dispara_no_save_do_user(self):
        user = baker.make(User, email="alguem@gmail.com")
        assert NormalizedEmail.objects.filter(user=user).exists()

    def test_sinal_ignora_user_sem_email(self):
        user = baker.make(User, email="")
        assert not NormalizedEmail.objects.filter(user=user).exists()

    def test_sinal_pula_quando_outro_usuario_jah_tem_o_valor_normalizado(self):
        primeiro = baker.make(User, email="foo@gmail.com")
        segundo = criar_conta_legada(email="f.o.o@gmail.com")
        segundo.first_name = "x"
        segundo.save()  # save completo de conta legada em colisão precisa continuar funcionando
        assert NormalizedEmail.objects.filter(user=primeiro).exists()
        assert not NormalizedEmail.objects.filter(user=segundo).exists()
        assert 1 == NormalizedEmail.objects.filter(value="foo@gmail.com").count()

    def test_sinal_atualiza_quando_email_muda(self):
        user = baker.make(User, email="antigo@gmail.com")
        user.email = "novo@gmail.com"
        user.save()
        assert "novo@gmail.com" == NormalizedEmail.objects.get(user=user).value

    def test_sinal_nao_consulta_banco_em_save_que_nao_toca_email(self):
        baker.make(User, username="x", email="x@example.com")
        user = User.objects.get(username="x")
        with CaptureQueriesContext(connection) as queries:
            user.save(update_fields=["last_login"])
        assert 1 == len(queries)
