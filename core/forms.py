import re

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext_lazy as _

from core.data_models import EmpresaTableConfig
from core.models import get_table_model
from utils.forms import FlagedReCaptchaField as ReCaptchaField


def numbers_only(value):
    return re.compile("[^0-9]").sub("", value)


def _resolve_field_by_type(person_type):
    if person_type == "pessoa-fisica":
        return "nome_socio"
    elif person_type == "pessoa-juridica":
        return "cnpj"


def _get_obj(field, identifier, person_type):
    if person_type == "pessoa-fisica":
        Socio = get_table_model("socios-brasil", "socio")
        return Socio.objects.filter(**{field: identifier}).first()

    elif person_type == "pessoa-juridica":
        Empresa = EmpresaTableConfig.get_model()
        try:
            return Empresa.objects.get_headquarter_or_branch(numbers_only(identifier))
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


class ContactForm(forms.Form):
    name = forms.CharField(required=True, label="Nome")
    email = forms.EmailField(required=True, label="E-mail")
    message = forms.CharField(
        required=True, label="Mensagem", widget=forms.Textarea(attrs={"class": "materialize-textarea"}),
    )
    captcha = ReCaptchaField()


class DatasetSearchForm(forms.Form):
    search = forms.CharField(label="Titulo ou Descrição")


def get_table_dynamic_form(table, cache=True):
    def config_dynamic_filter(model_field):
        dynamic_field = table.get_field(model_field.name)
        kwargs = {"required": False, "label": dynamic_field.title}
        field_factory = model_field.formfield

        # null values are being saved as "None"
        if dynamic_field.has_choices and dynamic_field.choices:
            kwargs["choices"] = [("", "Todos")] + [
                (c, c if c != "None" else "(vazio)") for c in dynamic_field.choices.get("data", [])
            ]
            field_factory = forms.ChoiceField

        return field_factory(**kwargs)

    model = table.get_model(cache=cache)
    fields = model.extra["filtering"]
    return forms.modelform_factory(model, fields=fields, formfield_callback=config_dynamic_filter)
