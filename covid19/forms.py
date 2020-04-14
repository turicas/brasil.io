from localflavor.br.br_states import STATE_CHOICES
from pathlib import Path

from django import forms
from django.core.validators import URLValidator

from covid19.models import StateSpreadsheet
from covid19.permissions import user_has_state_permission


def state_choices_for_user(user):
    if user.is_superuser:
        return list(STATE_CHOICES)

    choices = []
    for uf, name in STATE_CHOICES:
        if user_has_state_permission(user, uf):
            choices.append((uf, name))

    return choices


class StateSpreadsheetForm(forms.ModelForm):
    valid_file_suffixes = ['.csv', '.xls', '.xlsx', '.ods']
    boletim_urls = forms.CharField(
        widget=forms.Textarea,
        help_text="Lista de URLs do(s) boletim(s) com uma entrada por linha"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['state'].choices = state_choices_for_user(self.user)

    class Meta:
        model = StateSpreadsheet
        fields = ['date', 'state', 'file', 'boletim_urls', 'boletim_notes']

    def save(self, commit=True):
        spreadsheet = super().save(commit=False)
        spreadsheet.user = self.user
        if commit:
            spreadsheet.save()
        return spreadsheet

    def clean_boletim_urls(self):
        urls = self.cleaned_data['boletim_urls'].strip().split('\n')
        url_validator = URLValidator(message="Uma ou mais das URLs não são válidas.")
        for url in urls:
            url_validator(url)
        return urls

    def clean_file(self):
        file = self.cleaned_data['file']
        valid = self.valid_file_suffixes
        path = Path(file.name)

        if not path.suffix.lower() in valid:
            msg = f"Formato de planilha inválida. O arquivo precisa estar formatado como {valid}."
            raise forms.ValidationError(msg)

        # Acredito que vale muito a pena deixar toda a lógica de validação desse arquivo numa função seprarada  # noqa
        # TODO: https://github.com/turicas/brasil.io/issues/209
        # TODO: https://github.com/turicas/brasil.io/issues/210
        # TODO: https://github.com/turicas/brasil.io/issues/217
        return file
