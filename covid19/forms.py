import io
import os
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile

import rows
from django import forms
from django.core.validators import URLValidator
from localflavor.br.br_states import STATE_CHOICES

from covid19.exceptions import SpreadsheetValidationErrors
from covid19.models import StateSpreadsheet
from covid19.permissions import user_has_state_permission
from covid19.spreadsheet_validator import format_spreadsheet_rows_as_dict


def state_choices_for_user(user):
    if user.is_superuser:
        return list(STATE_CHOICES)

    choices = []
    for uf, name in STATE_CHOICES:
        if user_has_state_permission(user, uf):
            choices.append((uf, name))

    return choices


def import_xls(f_obj):
    content = f_obj.read()
    f_obj.seek(0)

    temp_xls = NamedTemporaryFile(suffix=".xls", delete=False)
    temp_xls.write(content)
    temp_xls.close()

    temp_file = Path(temp_xls.name)
    with open(temp_file, "rb") as temp_xls:
        data = rows.import_from_xls(temp_xls)

    os.remove(temp_file)
    return data


class StateSpreadsheetForm(forms.ModelForm):
    boletim_urls = forms.CharField(
        widget=forms.Textarea, help_text="Lista de URLs do(s) boletim(s) com uma entrada por linha"
    )
    boletim_notes = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text='Observações no boletim como "depois de publicar o boletim a secretaria postou no Twitter que teve mais uma morte".',  # noqa
    )
    skip_sum_cases = forms.BooleanField(required=False, label="Ignorar validação de soma de casos",)
    skip_sum_deaths = forms.BooleanField(required=False, label="Ignorar validação de soma de mortes",)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["state"].choices = state_choices_for_user(self.user)

        help = (
            'Caso necessário, baixe o arquivo modelo para os estados clicando nos botões acima entitulados "Modelo XX".'
        )
        if "state" in self.fields:
            self.fields["state"].help_text = help
        self.file_data_as_json = []
        self.data_warnings = []

    class Meta:
        model = StateSpreadsheet
        fields = ["date", "state", "file", "boletim_urls", "boletim_notes"]

    def save(self, commit=True):
        spreadsheet = super().save(commit=False)
        spreadsheet.user = self.user
        spreadsheet.table_data = self.file_data_as_json
        spreadsheet.warnings = self.data_warnings
        if commit:
            spreadsheet.save()
        return spreadsheet

    def clean_date(self):
        report_date = self.cleaned_data["date"]
        if report_date > date.today():
            raise forms.ValidationError("Campo não aceita datas futuras.")
        return report_date

    def clean_boletim_urls(self):
        urls = [u.strip() for u in self.cleaned_data["boletim_urls"].split("\n")]
        url_validator = URLValidator(message="Uma ou mais das URLs não são válidas.")
        for url in urls:
            url_validator(url)
        return urls

    def clean(self):
        cleaned_data = super().clean()
        fobj = cleaned_data.get("file")
        spreadsheet_date = cleaned_data.get("date")
        state = cleaned_data.get("state")

        if all([fobj, spreadsheet_date, state]):
            path = Path(fobj.name)
            suffix = path.suffix.lower()
            import_func_per_suffix = {
                ".csv": rows.import_from_csv,
                ".xls": import_xls,
                ".xlsx": rows.import_from_xlsx,
                ".ods": rows.import_from_ods,
            }

            import_func = import_func_per_suffix.get(suffix)
            if not import_func:
                valid = import_func_per_suffix.keys()
                msg = f"Formato de planilha inválida. O arquivo precisa estar formatado como {valid}."  # noqa
                raise forms.ValidationError(msg)

            file_data = io.BytesIO(fobj.read())
            fobj.seek(0)
            try:
                file_rows = import_func(file_data)
            except Exception as e:
                msg = f"Incoerência no formato do arquivo e sua extensão. Confirme se o conteúdo arquivo de fato corresponde a um {suffix} válido."
                raise forms.ValidationError(f"{msg} ERRO: {e}")

            try:
                self.file_data_as_json, self.data_warnings = format_spreadsheet_rows_as_dict(
                    file_rows,
                    spreadsheet_date,
                    state,
                    skip_sum_cases=cleaned_data.get("skip_sum_cases", False),
                    skip_sum_deaths=cleaned_data.get("skip_sum_deaths", False),
                )
            except SpreadsheetValidationErrors as exception:
                for error in exception.error_messages:
                    self.add_error(None, error)
