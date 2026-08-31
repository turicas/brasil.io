import datetime
import sys

import sentry_sdk
from django.core.management.base import BaseCommand

from core.entrega_emails import verificar_entrega_emails


class Command(BaseCommand):
    help = "Verifica a entrega de e-mails do django-mailer e reporta problemas ao Sentry"

    def add_arguments(self, parser):
        parser.add_argument(
            "--janela-minutos", type=int, default=60, help="Janela de análise das tentativas (padrão: 60)"
        )
        parser.add_argument(
            "--idade-maxima-fila-minutos",
            type=int,
            default=15,
            help="Tempo máximo de uma mensagem pronta esperar na fila antes de alertar (padrão: 15)",
        )

    def handle(self, *args, **options):
        problemas = verificar_entrega_emails(
            janela=datetime.timedelta(minutes=options["janela_minutos"]),
            idade_maxima_fila=datetime.timedelta(minutes=options["idade_maxima_fila_minutos"]),
        )
        if not problemas:
            self.stdout.write("Entrega de e-mails OK")
            return

        for problema in problemas:
            self.stderr.write(f"[{problema.tipo}] {problema.mensagem} {problema.detalhes}")
            with sentry_sdk.push_scope() as scope:
                scope.fingerprint = ["mail-delivery", problema.tipo]
                for chave, valor in problema.detalhes.items():
                    scope.set_extra(chave, valor)
                sentry_sdk.capture_message(problema.mensagem, level="error")
        sys.exit(1)
