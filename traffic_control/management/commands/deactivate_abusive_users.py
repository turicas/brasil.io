from django.core.management.base import BaseCommand

from traffic_control.commands import DeactivateAbusiveUsersCommand


class Command(BaseCommand):
    help = "Desativa usuários que abusaram da API (deep pagination) e envia e-mail explicando."

    def add_arguments(self, parser):
        parser.add_argument(
            "-h",
            "--hours-ago",
            type=int,
            default=None,
            help="Janela de tempo a considerar em horas (padrão: settings.API_ABUSIVE_USER_WINDOW_HOURS)",
        )
        parser.add_argument(
            "-t",
            "--threshold",
            type=int,
            default=None,
            help="Mínimo de bloqueios na janela para desativar (padrão: settings.API_ABUSIVE_USER_THRESHOLD)",
        )
        parser.add_argument(
            "-r",
            "--block-reason",
            action="append",
            default=None,
            dest="block_reasons",
            metavar="REASON",
            help="Tipos de bloqueio que contam para o critério (pode repetir). Padrão: deep_pagination_not_allowed.",
        )
        parser.add_argument(
            "-m",
            "--max-deactivations",
            type=int,
            default=None,
            help=(
                "Número máximo de contas desativadas nesta execução "
                f"(padrão: {DeactivateAbusiveUsersCommand.DEFAULT_MAX_DEACTIVATIONS}). "
                "Excedentes ficam para a próxima rodada."
            ),
        )
        parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            help="Lista candidatos sem desativar nem enviar e-mail.",
        )

    def handle(self, *args, **kwargs):
        DeactivateAbusiveUsersCommand.execute(
            hours_ago=kwargs["hours_ago"],
            threshold=kwargs["threshold"],
            block_reasons=kwargs["block_reasons"],
            max_deactivations=kwargs["max_deactivations"],
            dry_run=kwargs["dry_run"],
        )
