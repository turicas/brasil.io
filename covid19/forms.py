import os
import rows
from localflavor.br.br_states import STATE_CHOICES
from pathlib import Path
from tempfile import NamedTemporaryFile

from django import forms
from django.core.validators import URLValidator

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

    temp_xls = NamedTemporaryFile(suffix='.xls', delete=False)
    temp_xls.write(content)
    temp_xls.close()

    data = rows.import_from_xls(temp_xls)
    temp_file = Path(temp_xls.name)
    os.remove(temp_file)

    return data


class StateSpreadsheetForm(forms.ModelForm):
    boletim_urls = forms.CharField(
        widget=forms.Textarea,
        help_text="Lista de URLs do(s) boletim(s) com uma entrada por linha"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['state'].choices = state_choices_for_user(self.user)
        self.file_data_as_json = {}

    class Meta:
        model = StateSpreadsheet
        fields = ['date', 'state', 'file', 'boletim_urls', 'boletim_notes']

    def save(self, commit=True):
        spreadsheet = super().save(commit=False)
        spreadsheet.user = self.user
        spreadsheet.data = {
            "table": self.file_data_as_json,
            "errors": [],
            "warnings": [],
        }
        if commit:
            spreadsheet.save()
        return spreadsheet

    def clean_boletim_urls(self):
        urls = self.cleaned_data['boletim_urls'].strip().split('\n')
        url_validator = URLValidator(message="Uma ou mais das URLs não são válidas.")
        for url in urls:
            url_validator(url)
        return urls

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        spreadsheet_date = cleaned_data.get("date")
        state = cleaned_data.get("state")

        if all([file, spreadsheet_date, state]):
            path = Path(file.name)
            import_func_per_suffix = {
                '.csv': rows.import_from_csv,
                '.xls': import_xls,
                '.xlsx': rows.import_from_xlsx,
                '.ods': rows.import_from_ods,
            }

            import_func = import_func_per_suffix.get(path.suffix.lower())
            if not import_func:
                valid = import_func_per_suffix.keys()
                msg = f"Formato de planilha inválida. O arquivo precisa estar formatado como {valid}."  # noqa
                raise forms.ValidationError(msg)

            file_rows = import_func(file)
            self.file_data_as_json = format_spreadsheet_rows_as_dict(
                file_rows, spreadsheet_date, state
            )
