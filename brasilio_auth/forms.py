import re

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationFormUniqueEmail

from utils.forms import FlagedReCaptchaField as ReCaptchaField

USERNAME_REGEXP = re.compile(r"[^A-Za-z0-9_]")
PUNCT_REGEXP = re.compile("[-/ .]")
User = get_user_model()


def is_valid_username(username):
    return not (PUNCT_REGEXP.sub("", username).isdigit() or USERNAME_REGEXP.search(username))


class UserCreationForm(RegistrationFormUniqueEmail):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"type": "text", "class": "form-control"}), label=_("Usuário"), required=True
    )

    email = forms.EmailField(
        widget=forms.TextInput(attrs={"placeholder": "ex@mail.com", "type": "email", "class": "form-control"}),
        required=True,
    )
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text=_("Enter the same password as above, for verification."),
    )
    captcha = ReCaptchaField()
    subscribe_newsletter = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"type": "checkbox", "class": "form-check-input"},), required=False
    )

    class Meta:
        model = get_user_model()
        fields = ("username", "email")

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not is_valid_username(username):
            raise forms.ValidationError(
                "Nome de usuário pode conter apenas letras, números e '_' e não deve ser um documento"
            )
        elif username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Nome de usuário já existente (escolha um diferente).")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(f"Usuário com o email {email} já cadastrado.")
        return email


class TokenApiManagementForm(forms.Form):
    captcha = ReCaptchaField()
