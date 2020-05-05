from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.utils.translation import ugettext_lazy as _

from brasilio_auth.models import NewsletterSubscriber


class UserCreationForm(DjangoUserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"style": "text-transform: lowercase"}),)
    email = forms.EmailField()
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."),
    )
    subscribe_newsletter = forms.BooleanField(required=False)

    class Meta:
        model = get_user_model()
        fields = ("username", "email")

    def clean_username(self):
        username = self.cleaned_data.get("username", "")
        return username.lower()

    def save(self, *args, **kwargs):
        user = super(UserCreationForm, self).save(*args, **kwargs)
        if self.cleaned_data.get("subscribe_newsletter"):
            NewsletterSubscriber.objects.create(user=user)
        return user

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            if get_user_model().objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(f"Usuário com o email {email} já cadastrado.")
        return email
