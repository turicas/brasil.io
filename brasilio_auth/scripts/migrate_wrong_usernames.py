"""
Anteriormente, os usuários podiam cadastrar seu username utilizando o caractere
inválido '@'.
Este script corrige esse problema alterando os usernames que contem '@' por
variações únicas baseadas no nome de usuário e/ou no e-mail de cada registro.

Exemplo:
    old_username = 'name@'
    new_username = 'name'
"""
import csv
import string
from typing import Tuple

from django.contrib.auth import get_user_model
from rows.fields import slug

from brasilio_auth.forms import is_valid_username

User = get_user_model()
possible_chars = string.ascii_letters + string.digits + "_"


def possible_usernames(username: str, email: str, n_suffix: int = 10) -> Tuple[str, ...]:
    username = username.strip()
    email = email.strip()

    if username.lower() == email.lower():
        username = username.split("@")[0]
    else:
        if username.startswith("@"):
            username = username[1:]
        if username.endswith("@"):
            username = username[:-1]
        if "@" in username:
            stop = username.find("@")
            before, after = username[:stop], username[stop + 1 :]
            if "." in after:
                username = before
            else:
                username = "_".join(username.split("@"))

    email_parts = email.split("@")
    possible_2 = email_parts[0]
    possible_3 = email_parts[0] + "_" + email_parts[1].split(".")[0]
    possible_with_suffix = [f"{username}_{i}" for i in range(1, n_suffix)]
    return (username, possible_2, possible_3, *possible_with_suffix)


def migrate_usernames(filepath):
    with open(filepath, mode="w") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=["old_username", "new_username", "email"])
        writer.writeheader()
        for user in User.objects.all():
            if is_valid_username(user.username):
                continue

            # Define possible usernames based on current and remove any
            # non-allowed chars
            possible = [
                slug(username, permitted_chars=possible_chars)
                for username in possible_usernames(user.username, user.email)
            ]
            for username in possible:
                if not User.objects.filter(username=username).exists():
                    writer.writerow({"old_username": user.username, "new_username": username, "email": user.email})
                    user.username = username
                    user.save()
                    break
            print(f"ERROR: could not migrate {user} (tried: {', '.join(possible)})")


def run():
    filepath = "/data/fixed-usernames.csv"
    migrate_usernames(filepath)
