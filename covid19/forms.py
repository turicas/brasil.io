from localflavor.br.br_states import STATE_CHOICES

from django import forms

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
