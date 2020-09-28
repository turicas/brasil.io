import django_registration.backends.activation.views as registration_views
from django.urls import reverse_lazy

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
