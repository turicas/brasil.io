from django.db.models.signals import post_save
from django.dispatch import receiver

from covid19.models import StateSpreadsheet
from covid19.tasks import process_new_spreadsheet_task


@receiver(post_save, sender=StateSpreadsheet)
def process_new_spreadsheet_receiver(sender, instance, created, **kwargs):
    if created:
        StateSpreadsheet.objects.cancel_older_versions(instance)
        process_new_spreadsheet_task.delay(spreadsheet_pk=instance.pk)
