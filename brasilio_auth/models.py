from django.contrib.auth import get_user_model
from django.db import models


class NewsletterSubscriberQuerySet(models.QuerySet):
    def active(self):
        return self.filter(user__is_active=True)


class NewsletterSubscriber(models.Model):
    objects = NewsletterSubscriberQuerySet.as_manager()

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)


class ActivationResend(models.Model):
    """Registro de reenvio do e-mail de ativação a um usuário que nunca ativou a conta.

    Existe para tornar o reenvio idempotente: cada usuário recebe no máximo um reenvio, mesmo que o comando rode várias
    vezes ou seja interrompido no meio.
    """

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="activation_resend")
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reenvio de ativação"
        verbose_name_plural = "Reenvios de ativação"
        ordering = ["sent_at"]

    def __str__(self):
        return f"{self.user.username} ({self.sent_at:%Y-%m-%d %H:%M})"
