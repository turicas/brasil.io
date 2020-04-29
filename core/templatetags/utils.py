from django.template import Context, Library, Template
from django.conf import settings

from cryptography.fernet import Fernet


cipher_suite = Fernet(settings.FERNET_KEY)
register = Library()


def _getattr(obj, field, should_obfuscate):
    attr = field.name
    if hasattr(obj, attr):
        value = getattr(obj, attr)
    elif attr in obj:
        value = obj[attr]
    else:
        return None

    if should_obfuscate and field.obfuscate:
        value = obfuscate(value)
    return value


@register.filter(name="getattribute")
def getattribute(obj, field):
    return _getattr(obj, field, should_obfuscate=True)


@register.filter(name="getplainattribute")
def getplainattribute(obj, field):
    return _getattr(obj, field, should_obfuscate=False)


@register.filter(name="render")
def render(template_text, obj):
    template_text = "{% load utils %}" + template_text  # inception
    if not isinstance(obj, dict):
        obj = obj.__dict__
    return Template(template_text).render(Context(obj, use_l10n=False))


@register.filter(name="obfuscate")
def obfuscate(document):
    if document and len(document) == 11:
        document = "***{}***".format(document[3:8])
    return document


@register.filter(name="encrypt_if_needed")
def encrypt_if_needed(document):
    if obfuscate(document) != document:
        # If needs obfuscation (frontend), then needs encryption (URL)
        document = cipher_suite.encrypt(document.encode("ascii")).decode("ascii")
    return document
