import datetime
from dataclasses import dataclass, field

from django.utils import timezone
from mailer.models import RESULT_SUCCESS, Message, MessageLog


@dataclass
class Problema:
    tipo: str
    mensagem: str
    detalhes: dict = field(default_factory=dict)


def verificar_entrega_emails(
    janela: datetime.timedelta, idade_maxima_fila: datetime.timedelta, agora=None
) -> list[Problema]:
    """Verifica se o envio de e-mails via django-mailer está saudável.

    Três sintomas, cada um vira um `Problema` de tipo próprio (o Sentry agrupa por tipo):
    - `falhas`: tentativas de envio com erro dentro da janela (SMTP recusando, credencial, etc.)
    - `deferred`: mensagens que falharam e aguardam o `retry_deferred`
    - `fila_parada`: mensagem pronta para envio esperando há mais que `idade_maxima_fila`
      (indica `mail-worker` morto ou travado)

    O django-mailer registra falhas apenas como `logger.info`, por isso nada disso chega ao
    Sentry sozinho.
    """
    agora = agora or timezone.now()
    problemas = []

    inicio_janela = agora - janela
    tentativas = MessageLog.objects.filter(when_attempted__gte=inicio_janela)
    falhas = tentativas.exclude(result=RESULT_SUCCESS)
    total_falhas = falhas.count()
    if total_falhas:
        recentes = falhas.order_by("-when_attempted").values_list("log_message", flat=True)[:50]
        erros = list(dict.fromkeys(recentes))[:5]
        problemas.append(
            Problema(
                tipo="falhas",
                mensagem=f"{total_falhas} falha(s) de envio de e-mail nos últimos {int(janela.total_seconds() // 60)} min",
                detalhes={
                    "falhas": total_falhas,
                    "sucessos": tentativas.filter(result=RESULT_SUCCESS).count(),
                    "erros": erros,
                },
            )
        )

    total_deferred = Message.objects.deferred().count()
    if total_deferred:
        problemas.append(
            Problema(
                tipo="deferred",
                mensagem=f"{total_deferred} e-mail(s) aguardando reenvio (deferred)",
                detalhes={"deferred": total_deferred},
            )
        )

    mais_antiga = Message.objects.non_deferred().order_by("when_added").values_list("when_added", flat=True).first()
    if mais_antiga is not None and agora - mais_antiga > idade_maxima_fila:
        espera = agora - mais_antiga
        problemas.append(
            Problema(
                tipo="fila_parada",
                mensagem=f"E-mail na fila há {int(espera.total_seconds() // 60)} min sem tentativa de envio",
                detalhes={
                    "mais_antiga_em": mais_antiga.isoformat(),
                    "na_fila": Message.objects.non_deferred().count(),
                },
            )
        )

    return problemas
