from collections import defaultdict
from copy import deepcopy
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from localflavor.br.br_states import STATE_CHOICES

from covid19.exceptions import OnlyOneSpreadsheetException

User = get_user_model()


def format_spreadsheet_name(instance, filename):
    # file will be uploaded to MEDIA_ROOT/{uf}/casos-{uf}-{date}-{username}-{file_no}.{extension}"
    # where {file_no} is the number of uploaded files from that user for the same pair of state
    # and date. this is necessary to avoid other users from overwriting other spreadsheets
    uf = instance.state.upper()
    date = instance.date.isoformat()
    user = instance.user.username
    file_no = StateSpreadsheet.objects.filter_older_versions(instance).count() + 1
    suffix = Path(filename).suffix
    return f"covid19/{uf}/casos-{uf}-{date}-{user}-{file_no}{suffix}"  # noqa


class StateSpreadsheetQuerySet(models.QuerySet):
    def filter_older_versions(self, spreadsheet):
        qs = self.from_user(spreadsheet.user).from_state(spreadsheet.state).filter(date=spreadsheet.date,)
        if spreadsheet.id:
            qs = qs.exclude(id=spreadsheet.id)
        return qs

    def from_user(self, user):
        return self.filter(user=user)

    def from_state(self, state):
        return self.filter(state__iexact=state)

    def cancel_older_versions(self, spreadsheet):
        return self.filter_older_versions(spreadsheet).update(cancelled=True)

    def filter_active(self):
        return self.filter(cancelled=False)

    def filter_inactive(self):
        return self.filter(cancelled=True)

    def deployed(self):
        return self.filter(status=self.model.DEPLOYED)

    def pending_review(self):
        return self.filter(status__in=[self.model.UPLOADED, self.model.CHECK_FAILED])

    def deployable_for_state(self, state, avoid_peer_review_dupes=True, only_active=True):
        qs = self
        if only_active:
            qs = qs.filter_active()

        qs = qs.from_state(state).deployed().order_by("-date", "-created_at")
        if avoid_peer_review_dupes:
            qs = qs.distinct("date")
        return qs

    def most_recent_deployed(self, state, date=None):
        qs = self.deployable_for_state(state)
        if date:
            qs = qs.filter(date__lte=date)
        return qs.first()


class StateSpreadsheetManager(models.Manager):
    def get_state_data(self, state):
        """Return all state cases, grouped by date"""
        from covid19.spreadsheet_validator import TOTAL_LINE_DISPLAY
        from brazil_data.cities import get_city_info

        cases, reports = defaultdict(dict), {}
        qs = self.get_queryset()
        spreadsheets = qs.deployable_for_state(state, avoid_peer_review_dupes=False, only_active=False)
        dates_only_with_total = set()

        for spreadsheet in spreadsheets:
            date = spreadsheet.date
            if date in cases and date not in dates_only_with_total:
                continue
            elif date in cases and spreadsheet.only_with_total_entry:
                continue

            # Group all notes for a same URL to avoid repeated entries for date/url
            report_data = reports.get(date, defaultdict(list))
            for url in spreadsheet.boletim_urls:
                report_data[url].append(spreadsheet.boletim_notes or "")
            reports[date] = report_data

            if spreadsheet.only_with_total_entry:
                rows = [spreadsheet.get_total_data()]
                dates_only_with_total.add(date)
            elif date in dates_only_with_total:
                rows = spreadsheet.table_data_by_city.values()
                dates_only_with_total.remove(date)
            else:
                rows = spreadsheet.table_data

            for row in rows:
                city = row["city"]
                if city is None:
                    city = TOTAL_LINE_DISPLAY
                elif city != "Importados/Indefinidos":
                    city = get_city_info(city, state).city  # Fix city name
                cases[date][city] = {
                    "confirmed": row["confirmed"],
                    "deaths": row["deaths"],
                }

        # reports entries should be returned as a list
        reports_as_list = []
        for date, urls in reports.items():
            for url, notes in urls.items():
                reports_as_list.append(
                    {"date": date, "url": url, "notes": "\n".join([n.strip() for n in notes if n.strip()])}
                )

        return {
            "reports": reports_as_list,
            "cases": cases,
        }


def default_data_json():
    return {
        "table": [],
        "errors": [],
        "warnings": [],
    }


class StateSpreadsheet(models.Model):
    UPLOADED, CHECK_FAILED, DEPLOYED = 1, 2, 3
    STATUS_CHOICES = (
        (UPLOADED, "uploaded"),
        (CHECK_FAILED, "check-failed"),
        (DEPLOYED, "deployed"),
    )
    ONLY_WITH_TOTAL_WARNING = "Planilha importada somente com dados totais."

    objects = StateSpreadsheetManager.from_queryset(StateSpreadsheetQuerySet)()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.PROTECT, db_index=True)
    date = models.DateField(null=False, blank=False, db_index=True)
    state = models.CharField(max_length=2, null=False, blank=False, choices=STATE_CHOICES, db_index=True)
    file = models.FileField(upload_to=format_spreadsheet_name)
    peer_review = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    automatically_created = models.BooleanField(default=False)

    boletim_urls = ArrayField(models.TextField(), null=False, blank=False, help_text="Lista de URLs do(s) boletim(s)")
    boletim_notes = models.CharField(
        max_length=2000,
        default="",
        blank=True,
        help_text='Observações no boletim como "depois de publicar o boletim a secretaria postou no Twitter que teve mais uma morte".',  # noqa
    )

    # status da planilha: só aceitaremos planilhas sem erros, então quando ela
    # é subida, inicia-se um processo em background de checá-la conforme outra
    # planilha pro mesmo estado pra mesma data - esse worker é quem mudará o
    # status, o padrao qnd sobe a planilha e não tem erros é uploaded
    # (configurar celery ou rq)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=UPLOADED)

    # dados da planilha depois de parseada no form, já em JSON, pro worker não
    # precisar ler o arquivo (o validador da planilha no form vai ter que fazer
    # essa leitura, então ele faz, se estiver tudo ok já salva nesse campo pro
    # worker já trabalhar com os dados limpos e normalizados)
    data = models.JSONField(default=default_data_json)

    # por padrao é False, mas vira True se um mesmo usuário subir uma planilha
    # pro mesmo estado pra mesma data (ele cancela o upload anterior pra essa
    # data/estado automaticamente caso suba uma atualizacao)
    cancelled = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["date", "state"])]

    def __str__(self):
        active = "Ativa" if not self.cancelled else "Cancelada"
        return f"Planilha {active}: {self.state} - {self.date} por {self.user}"

    @property
    def active(self):
        return not self.cancelled

    @property
    def deployed(self):
        return self.status == self.DEPLOYED

    @property
    def table_data(self):
        return deepcopy(self.data["table"])

    @table_data.setter
    def table_data(self, data):
        self.data["table"] = deepcopy(data)

    @property
    def warnings(self):
        return deepcopy(self.data["warnings"])

    @warnings.setter
    def warnings(self, data):
        self.data["warnings"] = data

    @property
    def errors(self):
        return deepcopy(self.data["errors"])

    @errors.setter
    def errors(self, data):
        self.data["errors"] = data
        if data:
            self.status = StateSpreadsheet.CHECK_FAILED

    @property
    def sibilings(self):
        qs = StateSpreadsheet.objects.filter_active().from_state(self.state).filter(date=self.date)
        return qs.pending_review().exclude(pk=self.pk, user_id=self.user_id).order_by("created_at")

    @property
    def cities(self):
        return [c for c in self.table_data if c["place_type"] == "city"]

    @property
    def table_data_by_city(self):
        return {c["city"]: c for c in self.cities}

    @property
    def table_data_by_code(self):
        return {c["city_ibge_code"]: c for c in self.cities}

    @property
    def ready_to_import(self):
        return all([self.status == StateSpreadsheet.UPLOADED, not self.cancelled, self.peer_review,])

    @property
    def admin_url(self):
        return reverse("admin:covid19_statespreadsheet_change", args=[self.pk])

    @property
    def only_with_total_entry(self):
        return any([w for w in self.warnings if w.startswith(self.ONLY_WITH_TOTAL_WARNING)])

    def get_data_from_city(self, ibge_code):
        if ibge_code:  # ibge_code = None match for undefined data
            ibge_code = int(ibge_code)
        try:
            return [d for d in self.table_data if d["city_ibge_code"] == ibge_code][0]
        except IndexError:
            return None

    def get_total_data(self):
        try:
            return [d for d in self.table_data if d["place_type"] == "state"][0]
        except IndexError:
            return None

    def compare_to_spreadsheet(self, other):
        match = lambda e1, e2: e1 and e2 and e1["deaths"] == e2["deaths"] and e1["confirmed"] == e2["confirmed"]  # noqa

        errors = []
        if not self.date == other.date:
            errors.append("Datas das planilhas são diferentes.")
        if not self.state == other.state:
            errors.append("Estados das planilhas são diferentes.")

        if errors:
            return errors

        user = self.user.username
        other_user = other.user.username

        self_ibge_codes = set(self.table_data_by_code.keys())
        other_ibge_codes = set(other.table_data_by_code.keys())

        extra_self_ibge_codes = self_ibge_codes - other_ibge_codes
        for extra_self in extra_self_ibge_codes:
            extra = self.table_data_by_code[extra_self]["city"]
            errors.append(
                f"{extra} está na planilha (por {user}) mas não na outra usada para a comparação (por {other_user})."  # noqa
            )
        extra_other_ibge_codes = other_ibge_codes - self_ibge_codes
        for extra_other in extra_other_ibge_codes:
            extra = other.table_data_by_code[extra_other]["city"]
            errors.append(
                f"{extra} está na planilha usada para a comparação (por {other_user}) mas não na importada (por {user}).",  # noqa
            )

        self_len = len(self.table_data)
        other_len = len(other.table_data)
        if not errors and self_len != other_len:
            errors.append(
                f"Número de entradas finais divergem. A planilha de comparação (por {other_user}) possui {other_len} mas a importada (por {user}) possui {self_len}.",  # noqa
            )

        for entry in self.table_data:
            display = entry["city"] or "Total"
            if entry["place_type"] == "state":
                other_entry = other.get_total_data()
            else:
                other_entry = other.get_data_from_city(entry["city_ibge_code"])

            if entry["city_ibge_code"] not in extra_self_ibge_codes and not match(entry, other_entry):
                errors.append(f"Número de casos confirmados ou óbitos diferem para {display}.")
            elif other_entry:
                city, other_city = entry["city"], other_entry["city"]
                if city != other_city:
                    errors.append(f"Grafias diferentes para a cidade: {city} - {other_city}")

        return errors

    def link_to_matching_spreadsheet_peer(self):
        """
        Compare the spreadsheet with the sibiling ones with the possible outputs:

        1. raise OnlyOneSpreadsheetException
        2. return a tuple as (True, [])
        3. return a tuple as (False, ['error 1', 'error 2'])
        """
        if not self.sibilings.exists():
            raise OnlyOneSpreadsheetException()

        errors = []
        for sibiling_spreadsheet in self.sibilings:
            self.link_to(sibiling_spreadsheet)
            sibiling_spreadsheet.link_to(self)
            errors = self.compare_to_spreadsheet(sibiling_spreadsheet)
            if not errors:
                return True, []
            else:
                sibiling_spreadsheet.errors = errors
                self.errors = errors
                sibiling_spreadsheet.save()
                self.save()

        return False, errors

    def link_to(self, other):
        self.peer_review = other
        self.errors = []
        self.status = StateSpreadsheet.UPLOADED
        self.save()

    def import_to_final_dataset(self, notification_callable=None, automatically_created=False):
        if automatically_created:
            self.data["warnings"].insert(0, f"Importação automática disparada por {self.user.username}")
            self.user = User.objects.get(username=settings.COVID19_AUTO_IMPORT_USER)
            self.automatically_created = True
            self.link_to(self)

        self.refresh_from_db()
        if not self.ready_to_import:
            raise ValueError(f"{self} is not ready to be imported")

        self.status = StateSpreadsheet.DEPLOYED
        self.save()
        self.peer_review.status = StateSpreadsheet.DEPLOYED
        self.peer_review.save()

        if notification_callable:
            notification_callable(self)


class DailyBulletin(models.Model):
    updated_at = models.DateField(auto_now=True)
    created_at = models.DateField(auto_now_add=True)
    date = models.DateField(unique=True)
    image_url = models.URLField()
    detailed_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Boletim: {self.date.day}/{self.date.month}/{self.date.year}"

    @property
    def admin_url(self):
        return reverse("admin:covid19_dailybulletin_change", args=[self.pk])
