import django_registration.backends.activation.views as registration_views
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from api.models import NumMaxTokensExceeded, Token
from brasilio_auth.forms import UserCreationForm
from brasilio_auth.models import NewsletterSubscriber


class RegistrationView(registration_views.RegistrationView):
    # reference: https://github.com/ubernostrum/django-registration/blob/390a6c9eefa59917108cb60acd73dde51b0843f0/src/django_registration/backends/activation/views.py#L25
    template_name = "brasilio_auth/user_creation_form.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("brasilio_auth:sign_up_complete")
    email_body_template = "brasilio_auth/emails/activation_email_body.txt"
    email_subject_template = "brasilio_auth/emails/activation_email_subject.txt"
    disallowed_url = reverse_lazy("brasilio_auth:sign_up_disallowed")

    def create_inactive_user(self, form):
        user = super().create_inactive_user(form)
        if form.cleaned_data.get("subscribe_newsletter"):
            NewsletterSubscriber.objects.create(user=user)
        return user


class ActivationView(registration_views.ActivationView):
    # reference:  https://github.com/ubernostrum/django-registration/blob/390a6c9eefa59917108cb60acd73dde51b0843f0/src/django_registration/backends/activation/views.py#L106
    success_url = reverse_lazy("brasilio_auth:activation_complete")
    template_name = "brasilio_auth/activation_failed.html"

    def activate(self, *args, **kwargs):
        user = super().activate(*args, **kwargs)
        login(self.request, user)
        return user


@login_required()
def list_user_api_tokens(request):
    user = request.user
    tokens = user.auth_tokens.all()
    context = {"tokens": tokens, "num_tokens_available": Token.num_of_available_tokens(user)}
    return render(request, "brasilio_auth/list_user_api_tokens.html", context=context)


@login_required()
def create_new_api_token(request):
    try:
        token = Token.new_token_for_user(request.user)
        messages.add_message(request, messages.SUCCESS, f"Nova chave de API: <tt>{token}</tt>")
    except NumMaxTokensExceeded:
        msg = f"Você já possui número máximo de {settings.MAX_NUM_API_TOKEN_PER_USER} chaves de API."
        messages.add_message(request, messages.ERROR, msg)
    return redirect("brasilio_auth:list_api_tokens")


@login_required()
def delete_api_token(request, key):
    token = get_object_or_404(request.user.auth_tokens, key=key)
    token.delete()
    msg = "Chave de API deletada com sucesso."
    messages.add_message(request, messages.SUCCESS, msg)
    return redirect("brasilio_auth:list_api_tokens")
