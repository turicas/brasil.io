from django import forms

from core.models import Dataset


Socios = Dataset.objects.get(slug='socios-brasil').get_last_data_model()


def _resolve_field_by_type(person_type):
    if person_type == 'pessoa-fisica':
        return 'nome_socio'
    elif person_type == 'pessoa-juridica':
        return 'cnpj_empresa'


def _get_obj(field, identifier):
    return Socios.objects.filter(**{field: identifier}).first()


def _get_name(obj, person_type):
    if person_type == 'pessoa-fisica':
        return obj.nome_socio
    elif person_type == 'pessoa-juridica':
        return obj.nome_empresa


class TracePathForm(forms.Form):
    TYPE_CHOICES = [
        ('pessoa-fisica', 'Pessoa Física (nome completo)'),
        ('pessoa-juridica', 'Pessoa Jurídica (CNPJ)')
    ]

    origin_type = forms.ChoiceField(choices=TYPE_CHOICES, required=True)
    origin_identifier = forms.CharField(required=True)

    destination_type = forms.ChoiceField(choices=TYPE_CHOICES, required=True)
    destination_identifier = forms.CharField(required=True)

    def clean(self):
        cleaned_data = super().clean()
        origin_type = cleaned_data.get('origin_type')
        origin_identifier = cleaned_data.get('origin_identifier')
        destination_type = cleaned_data.get('destination_type')
        destination_identifier = cleaned_data.get('destination_identifier')

        origin_field = _resolve_field_by_type(origin_type)
        destination_field = _resolve_field_by_type(destination_type)
        origin = _get_obj(origin_field, origin_identifier)
        destination = _get_obj(destination_field, destination_identifier)

        if origin is None:
            self.add_error('origin_identifier', 'Name/document not found')
        else:
            cleaned_data['origin_name'] = _get_name(origin, origin_type)
        if destination is None:
            self.add_error('destination_identifier', 'Name/document not found')
        else:
            cleaned_data['destination_name'] = _get_name(destination, destination_type)

        return cleaned_data
