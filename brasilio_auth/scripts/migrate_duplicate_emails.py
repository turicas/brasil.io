from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import Lower, Trim
from tqdm import tqdm

from api.models import Token
from covid19.models import StateSpreadsheet


User = get_user_model()


def run():
    duplicate_emails = User.objects.annotate(
        email_lower_trim=Lower(Trim("email")),
    ).values("email_lower_trim").annotate(cnt=Count("email_lower_trim")).\
        filter(~Q(email_lower_trim=""), cnt__gt=1)

    for duplicate_email in tqdm(duplicate_emails):
        email_lower_trim = duplicate_email["email_lower_trim"]
        duplicate_users = User.objects.filter(
            email__icontains=email_lower_trim
        ).order_by("date_joined")
        first_joined_user = duplicate_users[0]
        last_joined_users = duplicate_users[1:]

        first_joined_user.email = email_lower_trim
        first_joined_user.save()

        query = ~Q(user=first_joined_user) & Q(user__email__icontains=email_lower_trim)

        Token.objects.filter(query).update(user=first_joined_user)
        StateSpreadsheet.objects.filter(query).update(user=first_joined_user)

        # duplicate users are deleted
        User.objects.filter(id__in=last_joined_users.values_list("id", flat=True)).delete()
