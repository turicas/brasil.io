from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from covid19.commands import UpdateStateTotalsCommand


class Command(BaseCommand):
    help = "Update state totals based on custom spreadsheet"

    def add_arguments(self, parser):
        parser.add_argument("--force", help="Força estados a serem atualizados (separados por vírgula)")
        parser.add_argument("--only", help="Execute comando apenas para esses estados (separados por vírgula)")

    def get_state_option(self, kwargs, name):
        return [state.strip().upper() for state in (kwargs.get(name, "") or "").split(",") if state.strip()]

    def handle(self, *args, **kwargs):
        force = self.get_state_option(kwargs, "force")
        only = self.get_state_option(kwargs, "only")

        username = "admin"
        print(f"Getting user object for {username}")
        user = get_user_model().objects.get(username=username)
        UpdateStateTotalsCommand.execute(user, force, only)
