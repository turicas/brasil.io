"""Checagens de unicidade de username e e-mail compartilhadas por cadastro, admin e signal de `User`."""

from django.contrib.auth import get_user_model

from brasilio_auth.models import NormalizedEmail
from brasilio_auth.validators import normalize_email_address


def username_em_colisao(username: str, excluir_id: int | None = None) -> bool:
    """Existe outra conta com esse username ignorando maiúsculas? (`auth_user.username` é único, mas case-sensitive.)"""
    if not username:
        return False
    return get_user_model().objects.filter(username__iexact=username).exclude(pk=excluir_id).exists()


def email_em_colisao(email: str, excluir_id: int | None = None) -> bool:
    """
    Existe outra conta com esse e-mail? Compara pelo normalizado (`NormalizedEmail`) e também pelo texto exato,
    porque contas antigas em colisão não têm `NormalizedEmail`.
    """
    if not email:
        return False
    normalizado = normalize_email_address(email)
    return (
        NormalizedEmail.objects.filter(value=normalizado).exclude(user_id=excluir_id).exists()
        or get_user_model().objects.filter(email__iexact=email.strip()).exclude(pk=excluir_id).exists()
    )
