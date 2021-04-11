import csv

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import Lower, Trim
from tqdm import tqdm

from api.models import Token
from covid19.models import StateSpreadsheet

User = get_user_model()


def migrate_duplicate_emails(filepath=None):
    filepath = filepath or "/data/duplicate_email_users.csv"

    duplicate_emails = (
        User.objects.annotate(email_lower_trim=Lower(Trim("email")),)
        .values("email_lower_trim")
        .annotate(cnt=Count("email_lower_trim"))
        .filter(~Q(email_lower_trim=""), cnt__gt=1)
    )

    with open(filepath, mode="w") as fobj:
        writer = csv.DictWriter(
            fobj,
            fieldnames=[
                "first_joined_username",
                "first_joined_userid",
                "later_joined_username",
                "later_joined_userid",
                "email",
            ],
        )
        writer.writeheader()

        for duplicate_email in tqdm(duplicate_emails):
            email_lower_trim = duplicate_email["email_lower_trim"]
            duplicate_users = User.objects.filter(email__icontains=email_lower_trim).order_by("date_joined")
            first_joined_user = duplicate_users[0]
            last_joined_users = duplicate_users[1:]

            first_joined_user.email = email_lower_trim
            first_joined_user.save()

            writer.writerows(
                [
                    {
                        "first_joined_username": first_joined_user.username,
                        "first_joined_userid": first_joined_user.id,
                        "later_joined_username": lj.username,
                        "later_joined_userid": lj.id,
                        "email": first_joined_user.email,
                    }
                    for lj in last_joined_users
                ]
            )

            query = ~Q(user=first_joined_user) & Q(user__email__icontains=email_lower_trim)

            Token.objects.filter(query).update(user=first_joined_user)
            StateSpreadsheet.objects.filter(query).update(user=first_joined_user)

            # duplicate users are deleted
            User.objects.filter(id__in=last_joined_users.values_list("id", flat=True)).delete()


def run():
    migrate_duplicate_emails()
