import re

from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationFormUniqueEmail

from brasilio_auth.unicidade import email_em_colisao, username_em_colisao
from brasilio_auth.validators import (
    normalize_email_address,
    validate_email_not_disposable,
    validate_email_not_phone_gmail_farm,
)
from utils.forms import FlagedReCaptchaField as ReCaptchaField

USERNAME_REGEXP = re.compile(r"[^A-Za-z0-9_]")
PUNCT_REGEXP = re.compile("[-/ .]")
User = get_user_model()


def is_valid_username(username):
    return not (PUNCT_REGEXP.sub("", username).isdigit() or USERNAME_REGEXP.search(username))


class UserCreationForm(RegistrationFormUniqueEmail):
    username = forms.CharField(
        widget=forms.TextInput(),
    )
    email = forms.EmailField()
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."),
    )
    captcha = ReCaptchaField(required=True)
    subscribe_newsletter = forms.BooleanField(required=False)

    class Meta:
        model = get_user_model()
        fields = ("username", "email")

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not is_valid_username(username):
            raise forms.ValidationError(
                "Nome de usuário pode conter apenas letras, números e '_' e não deve ser um documento"
            )
        elif username_em_colisao(username):
            raise forms.ValidationError("Nome de usuário já existente (escolha um diferente).")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        normalizado = normalize_email_address(email)
        validate_email_not_disposable(normalizado)
        validate_email_not_phone_gmail_farm(normalizado)
        if email_em_colisao(email):
            raise forms.ValidationError(f"Usuário com o email {email} já cadastrado.")
        return email


class UnicidadeAdminMixin:
    """Repete no Django Admin as checagens de username/e-mail do cadastro (o admin padrão só confere igualdade exata)."""

    def clean_username(self):
        username = self.cleaned_data["username"]
        if username_em_colisao(username, excluir_id=self.instance.pk):
            raise forms.ValidationError("Nome de usuário já existente (escolha um diferente).")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "")
        if email_em_colisao(email, excluir_id=self.instance.pk):
            raise forms.ValidationError(f"Usuário com o email {email} já cadastrado.")
        return email


class AdminUserCreationForm(UnicidadeAdminMixin, auth_forms.UserCreationForm):
    pass


class AdminUserChangeForm(UnicidadeAdminMixin, auth_forms.UserChangeForm):
    pass


class TokenApiManagementForm(forms.Form):
    captcha = ReCaptchaField(required=True)
