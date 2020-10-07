import django_registration.backends.activation.views as registration_views
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from api.models import NumMaxTokensExceeded, Token
from brasilio_auth.forms import UserCreationForm, TokenApiManagementForm
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


class CreateNewApiToken(FormView):
    template_name = "brasilio_auth/new_api_token_form.html"
    form_class = TokenApiManagementForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["num_tokens_available"] = Token.num_of_available_tokens(self.request.user)
        return ctx

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        try:
            token = Token.new_token_for_user(self.request.user)
            messages.add_message(self.request, messages.SUCCESS, f"Nova chave de API: <tt>{token}</tt>")
        except NumMaxTokensExceeded:
            msg = f"Você já possui número máximo de {settings.MAX_NUM_API_TOKEN_PER_USER} chaves de API."
            messages.add_message(self.request, messages.ERROR, msg)
        return redirect("brasilio_auth:list_api_tokens")

create_new_api_token = login_required(CreateNewApiToken.as_view())


@login_required()
def delete_api_token(request, key):
    token = get_object_or_404(request.user.auth_tokens, key=key)
    token.delete()
    msg = "Chave de API deletada com sucesso."
    messages.add_message(request, messages.SUCCESS, msg)
    return redirect("brasilio_auth:list_api_tokens")


def api_token_demo_usage(request, key):
    return render(request, "brasilio_auth/api_token_sample_usage.html", context={"key": key})
