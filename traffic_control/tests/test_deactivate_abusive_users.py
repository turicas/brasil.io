from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker

from traffic_control.commands import DeactivateAbusiveUsersCommand
from traffic_control.models import BlockedRequest

User = get_user_model()


def _criar_blocos(quantidade, *, user, block_reason="deep_pagination_not_allowed", status_code=400, horas_atras=1):
    timestamp = timezone.now() - timedelta(hours=horas_atras)
    objs = [
        BlockedRequest(
            request_data={
                "user_id": user.id if user else None,
                "block_reason": block_reason,
                "path": "/api/v1/dataset/sample/sample_table/data/",
            },
            user=user,
            block_reason=block_reason,
            status_code=status_code,
            path="/api/v1/dataset/sample/sample_table/data/",
            source_ip="1.2.3.4",
        )
        for _ in range(quantidade)
    ]
    criados = BlockedRequest.objects.bulk_create(objs)
    for obj in criados:
        obj.created_at = timestamp
    BlockedRequest.objects.bulk_update(criados, ["created_at"])
    return criados


@override_settings(
    API_ABUSIVE_USER_THRESHOLD=5,
    API_ABUSIVE_USER_WINDOW_HOURS=24,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class DeactivateAbusiveUsersCommandTests(TestCase):
    def setUp(self):
        self.abuser = baker.make(User, username="abuser", email="abuser@example.com", is_active=True)
        self.normal = baker.make(User, username="normal", email="normal@example.com", is_active=True)
        baker.make("api.Token", user=self.abuser)
        baker.make("api.Token", user=self.abuser)
        mail.outbox = []

    def test_desativa_usuario_acima_do_threshold_e_apaga_tokens(self):
        _criar_blocos(10, user=self.abuser)
        DeactivateAbusiveUsersCommand.execute()
        self.abuser.refresh_from_db()
        assert self.abuser.is_active is False
        assert 0 == self.abuser.auth_tokens.count()
        assert 1 == len(mail.outbox)
        email = mail.outbox[0]
        assert [self.abuser.email] == email.to
        assert "desativada" in email.subject.lower()
        assert self.abuser.username in email.body
        assert "10" in email.body
        assert "24" in email.body
        assert "https://brasil.io/datasets/" in email.body

    def test_nao_desativa_abaixo_do_threshold(self):
        _criar_blocos(4, user=self.normal)
        DeactivateAbusiveUsersCommand.execute()
        self.normal.refresh_from_db()
        assert self.normal.is_active is True
        assert 0 == len(mail.outbox)

    def test_ignora_block_reason_fora_do_filtro_padrao(self):
        _criar_blocos(10, user=self.normal, block_reason="invalid_token", status_code=401)
        DeactivateAbusiveUsersCommand.execute()
        self.normal.refresh_from_db()
        assert self.normal.is_active is True

    def test_aceita_block_reasons_alternativos_via_parametro(self):
        _criar_blocos(10, user=self.normal, block_reason="throttled", status_code=429)
        DeactivateAbusiveUsersCommand.execute(block_reasons=["throttled"])
        self.normal.refresh_from_db()
        assert self.normal.is_active is False

    def test_aceita_lista_de_block_reasons_combinados(self):
        _criar_blocos(3, user=self.normal, block_reason="deep_pagination_not_allowed")
        _criar_blocos(3, user=self.normal, block_reason="throttled", status_code=429)
        DeactivateAbusiveUsersCommand.execute(block_reasons=["deep_pagination_not_allowed", "throttled"])
        self.normal.refresh_from_db()
        assert self.normal.is_active is False

    def test_ignora_bloqueios_fora_da_janela(self):
        _criar_blocos(10, user=self.normal, horas_atras=100)
        DeactivateAbusiveUsersCommand.execute()
        self.normal.refresh_from_db()
        assert self.normal.is_active is True

    def test_ignora_usuarios_ja_inativos(self):
        self.abuser.is_active = False
        self.abuser.save(update_fields=["is_active"])
        _criar_blocos(10, user=self.abuser)
        DeactivateAbusiveUsersCommand.execute()
        assert 0 == len(mail.outbox)

    def test_ignora_requisicoes_anonimas(self):
        _criar_blocos(10, user=None)
        DeactivateAbusiveUsersCommand.execute()
        assert 0 == len(mail.outbox)

    def test_dry_run_nao_altera_nada(self):
        _criar_blocos(10, user=self.abuser)
        DeactivateAbusiveUsersCommand.execute(dry_run=True)
        self.abuser.refresh_from_db()
        assert self.abuser.is_active is True
        assert 2 == self.abuser.auth_tokens.count()
        assert 0 == len(mail.outbox)

    def test_max_deactivations_limita_processados_por_rodada(self):
        usuarios = [
            baker.make(User, username=f"abuser_extra_{i}", email=f"a{i}@example.com", is_active=True) for i in range(5)
        ]
        for usuario in usuarios:
            _criar_blocos(10, user=usuario)
        DeactivateAbusiveUsersCommand.execute(max_deactivations=2)
        ativos_apos = [user for user in usuarios if User.objects.get(pk=user.pk).is_active]
        assert 3 == len(ativos_apos)
        assert 2 == len(mail.outbox)

    def test_threshold_e_janela_via_parametro(self):
        _criar_blocos(3, user=self.abuser)
        DeactivateAbusiveUsersCommand.execute(threshold=3, hours_ago=24)
        self.abuser.refresh_from_db()
        assert self.abuser.is_active is False

    def test_usuario_sem_email_eh_desativado_mas_sem_envio(self):
        sem_email = baker.make(User, username="semail", email="", is_active=True)
        _criar_blocos(10, user=sem_email)
        DeactivateAbusiveUsersCommand.execute()
        sem_email.refresh_from_db()
        assert sem_email.is_active is False
        assert 0 == len(mail.outbox)
