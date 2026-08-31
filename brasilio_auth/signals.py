from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from brasilio_auth.models import NormalizedEmail
from brasilio_auth.validators import normalize_email_address


@receiver(post_save, sender=get_user_model())
def sync_normalized_email(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw or not instance.email:
        return
    if update_fields is not None and "email" not in update_fields:  # Ex.: `last_login` a cada login
        return
    normalizado = normalize_email_address(instance.email)
    existente = getattr(instance, "normalized_email", None)
    if existente and existente.value == normalizado:
        return
    if NormalizedEmail.objects.filter(value=normalizado).exclude(user=instance).exists():
        return
    NormalizedEmail.objects.update_or_create(user=instance, defaults={"value": normalizado})
