from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from brasilio_auth.models import ActivationResend, NewsletterSubscriber
from brasilio_auth.views import RegistrationView


def subscribers_as_csv_rows(include_header=True):
    rows = []
    if include_header:
        rows.append(("username", "email"))

    qs = NewsletterSubscriber.objects.select_related("user").active()
    for user in [subscriber.user for subscriber in qs]:
        rows.append((user.username, user.email))

    return rows


class ResendActivationView(RegistrationView):
    """Reaproveita a geração de chave e o envio do django-registration com um e-mail próprio.

    Fora de uma requisição HTTP não há `request`; o host do link vem por parâmetro.
    """

    email_body_template = "brasilio_auth/emails/resend_activation_email_body.txt"
    email_subject_template = "brasilio_auth/emails/resend_activation_email_subject.txt"
    request = None

    def __init__(self, host, **kwargs):
        super().__init__(**kwargs)
        self.host = host

    def get_email_context(self, activation_key):
        return {
            "activation_key": activation_key,
            "expiration_days": settings.ACCOUNT_ACTIVATION_DAYS,
            "request": None,
            "scheme": "https",
            "site": self.host,
        }


def users_pending_activation_resend(joined_after, joined_before):
    """Usuários inativos cadastrados no período que ainda não receberam reenvio, dos mais antigos aos mais novos."""
    return (
        get_user_model()
        .objects.filter(
            is_active=False,
            date_joined__gte=joined_after,
            date_joined__lt=joined_before,
            activation_resend__isnull=True,
        )
        .exclude(email="")
        .order_by("date_joined")
    )


def resend_activation_emails(joined_after, joined_before, limit, host, dry_run=False):
    """Reenvia o e-mail de ativação a até `limit` usuários e registra cada envio em `ActivationResend`.

    O limite existe para espaçar os envios entre execuções (reputação junto aos provedores).
    Cada usuário é tratado em transação própria: se o processo cair no meio, os já enviados
    ficam registrados e não recebem de novo.
    """
    view = ResendActivationView(host=host)
    enviados = []
    for user in users_pending_activation_resend(joined_after, joined_before)[:limit]:
        if not dry_run:
            with transaction.atomic():
                ActivationResend.objects.create(user=user)
                view.send_activation_email(user)
        enviados.append(user)
    return enviados
