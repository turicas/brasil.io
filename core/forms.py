import re

from captcha.fields import ReCaptchaField
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext_lazy as _

from core.models import get_table_model
from core.util import get_company_by_document


def numbers_only(value):
    return re.compile("[^0-9]").sub("", value)


def _resolve_field_by_type(person_type):
    if person_type == "pessoa-fisica":
        return "nome_socio"
    elif person_type == "pessoa-juridica":
        return "cnpj"


def _get_obj(field, identifier, person_type):
    if person_type == "pessoa-fisica":
        Socios = get_table_model("socios-brasil", "socios")
        return Socios.objects.filter(**{field: identifier}).first()
    elif person_type == "pessoa-juridica":
        try:
            return get_company_by_document(numbers_only(identifier))
        except ValueError:
            raise ValidationError(
                _("Invalid value: %(value)s"), params={"value": identifier},
            )
        except ObjectDoesNotExist:
            return None


def _get_name(obj, person_type):
    if person_type == "pessoa-fisica":
        return obj.nome_socio
    elif person_type == "pessoa-juridica":
        return obj.name


class TracePathForm(forms.Form):
    TYPE_CHOICES = [("pessoa-fisica", "Pessoa Física (nome completo)"), ("pessoa-juridica", "Pessoa Jurídica (CNPJ)")]

    origin_type = forms.ChoiceField(choices=TYPE_CHOICES, required=True)
    origin_identifier = forms.CharField(required=True)

    destination_type = forms.ChoiceField(choices=TYPE_CHOICES, required=True)
    destination_identifier = forms.CharField(required=True)

    def clean(self):
        cleaned_data = super().clean()
        origin_type = cleaned_data.get("origin_type")
        origin_identifier = cleaned_data.get("origin_identifier")
        destination_type = cleaned_data.get("destination_type")
        destination_identifier = cleaned_data.get("destination_identifier")

        origin_field = _resolve_field_by_type(origin_type)
        destination_field = _resolve_field_by_type(destination_type)
        origin = _get_obj(origin_field, origin_identifier, origin_type)
        destination = _get_obj(destination_field, destination_identifier, destination_type)

        if origin is None:
            self.add_error("origin_identifier", "Name/document not found")
        else:
            cleaned_data["origin_name"] = _get_name(origin, origin_type)
        if destination is None:
            self.add_error("destination_identifier", "Name/document not found")
        else:
            cleaned_data["destination_name"] = _get_name(destination, destination_type)

        return cleaned_data


class CompanyGroupsForm(forms.Form):
    identifier = forms.CharField(required=True, label="CNPJ")

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data["identifier"]
        for char in "./-":
            identifier = identifier.replace(char, "")
        company = _get_obj("", identifier, "pessoa-juridica")
        if not company:
            self.add_error("identifier", "Document not found")
        else:
            cleaned_data["company"] = company
        return cleaned_data


class ContactForm(forms.Form):
    name = forms.CharField(required=True, label="Nome")
    email = forms.EmailField(required=True, label="E-mail")
    message = forms.CharField(
        required=True, label="Mensagem", widget=forms.Textarea(attrs={"class": "materialize-textarea"}),
    )
    captcha = ReCaptchaField()


class DatasetSearchForm(forms.Form):
    search = forms.CharField(label="Titulo ou Descrição")
