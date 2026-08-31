import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from brasilio_auth.services import resend_activation_emails, users_pending_activation_resend


def parse_date(value):
    return datetime.datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.get_current_timezone())


class Command(BaseCommand):
    help = (
        "Reenvia o e-mail de ativação a usuários inativos cadastrados no período (útil quando o "
        "mail-worker ficou parado e os links expiraram). Cada usuário recebe no máximo um reenvio."
    )

    def add_arguments(self, parser):
        parser.add_argument("joined_after", type=parse_date, help="Cadastro a partir de (YYYY-MM-DD)")
        parser.add_argument("joined_before", type=parse_date, help="Cadastro antes de (YYYY-MM-DD)")
        parser.add_argument("-l", "--limit", type=int, default=20, help="Máximo de e-mails por execução (padrão: 20)")
        parser.add_argument(
            "-H", "--host", default="brasil.io", help="Host usado no link de ativação (padrão: brasil.io)"
        )
        parser.add_argument("-d", "--dry-run", action="store_true", help="Só lista quem receberia, sem enviar")

    def handle(self, *args, **options):
        pendentes = users_pending_activation_resend(options["joined_after"], options["joined_before"]).count()
        enviados = resend_activation_emails(
            joined_after=options["joined_after"],
            joined_before=options["joined_before"],
            limit=options["limit"],
            host=options["host"],
            dry_run=options["dry_run"],
        )
        verbo = "Receberiam" if options["dry_run"] else "Enviados"
        for user in enviados:
            self.stdout.write(f"  {user.date_joined:%Y-%m-%d} {user.username} <{user.email}>")
        self.stdout.write(f"{verbo}: {len(enviados)} de {pendentes} pendentes; restam {pendentes - len(enviados)}")
