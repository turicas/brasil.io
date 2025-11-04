from django.conf import settings
from django.core.mail import send_mail
from django_rq import job

from clipping.models import Clipping


@job
def send_clipping_mail(pk):
    obj = Clipping.objects.filter(pk=pk).select_related("added_by").first()
    send_mail(
        f"{settings.EMAIL_SUBJECT_PREFIX}Novo clippping",
        f"Clipping adicionado por {obj.added_by.username}: {obj.title} ({obj.get_category_display()}) / {obj.url}",
        settings.DEFAULT_FROM_EMAIL,
        ["contato@brasil.io"],
        fail_silently=False,
    )
