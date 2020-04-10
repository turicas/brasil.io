from pathlib import Path
from localflavor.br.br_states import STATE_CHOICES

from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField


def format_spreadsheet_name(instance, filename):
    # file will be uploaded to MEDIA_ROOT/{uf}/casos-{uf}-{date}-{username}-{file_no}.{extension}"
    # where {file_no} is the number of uploaded files from that user for the same pair of state
    # and date. this is necessary to avoid other users from overwriting other spreadsheets
    uf = instance.state
    date = instance.date.isoformat()
    user = instance.user.username
    file_no = StateSpreadsheet.objects.filter_older_versions(instance).count() + 1
    suffix = Path(filename).suffix
    return f'covid19/{uf}/casos-{uf}-{date}-{user}-{file_no}{suffix}'  # noqa


class StateSpreadsheetQuerySet(models.QuerySet):

    def filter_older_versions(self, spreadsheet):
        qs = self.filter(
            state=spreadsheet.state,
            user=spreadsheet.user,
            date=spreadsheet.date,
        )
        if spreadsheet.id:
            qs = qs.exclude(id=spreadsheet.id)
        return qs


class StateSpreadsheet(models.Model):
    STATUS_CHOICES = (
        (1, "uploaded"),
        (2, "check-failed"),
        (3, "deployed"),
    )

    objects = StateSpreadsheetQuerySet.as_manager()

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(get_user_model(), null=False, blank=False, on_delete=models.PROTECT)
    date = models.DateField(null=False, blank=False)
    state = models.CharField(max_length=2, null=False, blank=False, choices=STATE_CHOICES)
    file = models.FileField(upload_to=format_spreadsheet_name)

    # lista de URLs que o voluntário deverá preencher do(s) boletim(ns) que ele
    # acessou para criar a planilha:
    boletim_urls = ArrayField(models.TextField(), null=False, blank=False)

    # observações no boletim, como: "depois de publicar o boletim, secretaria
    # postou no twitter que teve mais uma morte"
    boletim_notes = models.CharField(max_length=1023, default='', blank=True)

    # status da planilha: só aceitaremos planilhas sem erros, então quando ela
    # é subida, inicia-se um processo em background de checá-la conforme outra
    # planilha pro mesmo estado pra mesma data - esse worker é quem mudará o
    # status, o padrao qnd sobe a planilha e não tem erros é uploaded
    # (configurar celery ou rq)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)

    # dados da planilha depois de parseada no form, já em JSON, pro worker não
    # precisar ler o arquivo (o validador da planilha no form vai ter que fazer
    # essa leitura, então ele faz, se estiver tudo ok já salva nesse campo pro
    # worker já trabalhar com os dados limpos e normalizados)
    data = JSONField(default=dict)

    # por padrao é False, mas vira True se um mesmo usuário subir uma planilha
    # pro mesmo estado pra mesma data (ele cancela o upload anterior pra essa
    # data/estado automaticamente caso suba uma atualizacao)
    cancelled = models.BooleanField(default=False)
