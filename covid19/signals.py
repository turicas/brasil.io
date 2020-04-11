from django.db.models.signals import post_save
from django.dispatch import receiver

from covid19.models import StateSpreadsheet


@receiver(post_save, sender=StateSpreadsheet)
def process_new_spreadsheet(sender, instance, created, **kwargs):
    if created:
        StateSpreadsheet.objects.cancel_older_versions(instance)
        # TODO https://github.com/turicas/brasil.io/issues/211
        # TODO https://github.com/turicas/brasil.io/issues/212
