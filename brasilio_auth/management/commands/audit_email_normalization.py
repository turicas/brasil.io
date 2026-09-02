from collections import defaultdict

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from brasilio_auth.validators import normalize_email_address

User = get_user_model()


class Command(BaseCommand):
    help = "Lista usuários cujo e-mail mudaria sob normalização ou cujo normalizado colide com outro usuário."

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--only-duplicates",
            action="store_true",
            help="Lista apenas casos em que dois ou mais usuários têm o mesmo e-mail normalizado.",
        )
        parser.add_argument(
            "-i",
            "--include-inactive",
            action="store_true",
            help="Inclui usuários com is_active=False (padrão: apenas ativos).",
        )

    def handle(self, *args, only_duplicates, include_inactive, **opts):
        qs = User.objects.all() if include_inactive else User.objects.filter(is_active=True)
        por_normalizado = defaultdict(list)
        for user in qs.iterator():
            normalizado = normalize_email_address(user.email)
            por_normalizado[normalizado].append(user)

        if only_duplicates:
            por_normalizado = {chave: users for chave, users in por_normalizado.items() if len(users) > 1}

        total_mudariam = 0
        total_colidem = 0
        for normalizado, users in por_normalizado.items():
            for user in users:
                if user.email != normalizado:
                    total_mudariam += 1
                duplicado = "DUPLICATE" if len(users) > 1 else ""
                self.stdout.write(
                    f"id={user.id} username={user.username} email={user.email!r} normalized={normalizado!r} {duplicado}"
                )
            if len(users) > 1:
                total_colidem += len(users)
        self.stdout.write(f"\nTotal de e-mails que mudariam sob normalização: {total_mudariam}")
        self.stdout.write(f"Total de usuários envolvidos em colisões: {total_colidem}")
