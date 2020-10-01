from captcha.fields import ReCaptchaField
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationFormUniqueEmail


class UserCreationForm(RegistrationFormUniqueEmail):
    username = forms.CharField(widget=forms.TextInput(attrs={"style": "text-transform: lowercase"}),)
    email = forms.EmailField()
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."),
    )
    captcha = ReCaptchaField()
    subscribe_newsletter = forms.BooleanField(required=False)

    class Meta:
        model = get_user_model()
        fields = ("username", "email")

    def clean_username(self):
        username = self.cleaned_data.get("username", "")
        return username.lower()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            if get_user_model().objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(f"Usuário com o email {email} já cadastrado.")
        return email
