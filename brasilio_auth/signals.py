from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from brasilio_auth.models import NormalizedEmail
from brasilio_auth.unicidade import email_em_colisao, username_em_colisao
from brasilio_auth.validators import normalize_email_address

CAMPOS_UNICOS = {"username", "email"}


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
    # A constraint unique em `value` é a autoridade final: se outra transação conquistar o valor entre o `exists()`
    # e o `update_or_create` (corrida), perdemos o `IntegrityError` e a conta fica sem linha - mesmo efeito do
    # filtro de colisão acima. Troca consciente de dono do valor deve manipular `NormalizedEmail` explicitamente.
    try:
        with transaction.atomic():
            NormalizedEmail.objects.update_or_create(user=instance, defaults={"value": normalizado})
    except IntegrityError:
        pass


@receiver(pre_save, sender=get_user_model())
def impede_novas_colisoes(sender, instance, raw=False, update_fields=None, **kwargs):
    """
    Última barreira contra username/e-mail duplicados, por qualquer caminho (admin, shell, `createsuperuser`).
    Só olha campos que estão mudando: contas antigas que já colidem continuam podendo ser salvas sem tocar neles.
    """
    if raw:
        return
    campos = CAMPOS_UNICOS if update_fields is None else CAMPOS_UNICOS & set(update_fields)
    if not campos:
        return
    if instance.pk:
        atual = sender.objects.filter(pk=instance.pk).values("username", "email").first()
        if atual:
            campos = {campo for campo in campos if getattr(instance, campo) != atual[campo]}
    if "username" in campos and username_em_colisao(instance.username, excluir_id=instance.pk):
        raise ValidationError({"username": "Nome de usuário já existente (escolha um diferente)."})
    if "email" in campos and email_em_colisao(instance.email, excluir_id=instance.pk):
        raise ValidationError({"email": f"Usuário com o email {instance.email} já cadastrado."})
