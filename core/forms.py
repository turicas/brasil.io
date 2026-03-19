import re

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _

from core.data_models import EmpresaTableConfig
from core.models import get_table_model
from utils.forms import FlagedReCaptchaField as ReCaptchaField

RE_HTML_TAG = re.compile(r"<[^>]+>")
RE_CARACTERES_INVALIDOS_NOME = re.compile(r'[<>"\'\\/\x00-\x1f]')
RE_NON_LATIN = re.compile(
    r"[\u0400-\u04FF"  # cirílico
    r"\u0600-\u06FF"  # árabe
    r"\u4e00-\u9fff"  # CJK
    r"\u3040-\u309f"  # hiragana
    r"\u30a0-\u30ff"  # katakana
    r"\uAC00-\uD7AF"  # hangul
    r"]"
)
RE_SHORTENED_URL = re.compile(
    r"(?:https?://)?(?:"
    r"tinyurl\.com|bit\.ly|cutt\.ly|hop\.cx|is\.gd|v\.gd|"
    r"ow\.ly|rb\.gy|psee\.io|t\.co/|shorturl\.at|u\.to/"
    r")",
    re.IGNORECASE,
)
RE_BBCODE = re.compile(r"\[(url|img|b|i|color)[\]=]", re.IGNORECASE)
RE_URL = re.compile(r"https?://\S+", re.IGNORECASE)
MAX_URLS_MENSAGEM = 2
NOME_MAX_LENGTH = 200


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
                _("Invalid value: %(value)s"),
                params={"value": identifier},
            )
        except ObjectDoesNotExist:
            return None


def _get_name(obj, person_type):
    if person_type == "pessoa-fisica":
        return obj.nome_socio
    elif person_type == "pessoa-juridica":
        return obj.name


def validar_texto_sem_html(valor: str, nome_campo: str) -> str:
    valor = valor.strip()
    if RE_HTML_TAG.search(valor):
        raise forms.ValidationError(f"O campo {nome_campo} não pode conter HTML.")
    return valor


def validar_mensagem_contato(valor: str) -> str:
    valor = valor.strip()
    if not valor:
        raise forms.ValidationError("A mensagem é obrigatória.")
    valor = validar_texto_sem_html(valor, "mensagem")
    if (
        RE_NON_LATIN.search(valor)
        or RE_SHORTENED_URL.search(valor)
        or RE_BBCODE.search(valor)
        or len(RE_URL.findall(valor)) > MAX_URLS_MENSAGEM
    ):
        raise forms.ValidationError("Sua mensagem foi bloqueada pelo filtro anti-SPAM.")
    return valor


def sanitizar_nome_para_email(nome: str) -> str:
    """Remove caracteres que quebram o parsing de endereço RFC 5322"""
    nome = re.sub(r"<[^>]*>", "", nome)
    nome = re.sub(r'[<>"\\\x00-\x1f]', "", nome)
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome


class ContactForm(forms.Form):
    name = forms.CharField(required=True, label="Nome", max_length=NOME_MAX_LENGTH)
    email = forms.EmailField(required=True, label="E-mail")
    message = forms.CharField(
        required=True,
        label="Mensagem",
        widget=forms.Textarea(attrs={"class": "materialize-textarea"}),
    )
    captcha = ReCaptchaField()

    def clean_name(self):
        valor = self.cleaned_data["name"].strip()
        if not valor:
            raise forms.ValidationError("O nome é obrigatório.")
        valor = validar_texto_sem_html(valor, "nome")
        if RE_CARACTERES_INVALIDOS_NOME.search(valor):
            raise forms.ValidationError("O nome contém caracteres inválidos.")
        if RE_NON_LATIN.search(valor):
            raise forms.ValidationError("O nome contém caracteres não suportados.")
        return valor

    def clean_message(self):
        return validar_mensagem_contato(self.cleaned_data["message"])


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
