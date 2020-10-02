from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.views.generic.base import TemplateView

from brasilio_auth import views
from core.middlewares import disable_non_logged_user_cache

login = auth_views.LoginView.as_view(template_name="brasilio_auth/login.html")
logout = auth_views.LogoutView.as_view()

password_reset = auth_views.PasswordResetView.as_view(
    template_name="brasilio_auth/password_reset.html",
    success_url=reverse_lazy("brasilio_auth:password_reset_done"),
    email_template_name="brasilio_auth/emails/password_reset_email.html",
    subject_template_name="brasilio_auth/emails/password_reset_subject.txt",
)
password_reset_done = auth_views.PasswordResetDoneView.as_view(template_name="brasilio_auth/password_reset_done.html")
password_reset_confirm = auth_views.PasswordResetConfirmView.as_view(
    template_name="brasilio_auth/password_reset_form.html",
    success_url=reverse_lazy("brasilio_auth:password_reset_complete"),
)
password_reset_complete = auth_views.PasswordResetCompleteView.as_view(
    template_name="brasilio_auth/password_reset_complete.html"
)

app_name = "brasilio_auth"
urlpatterns = (
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("troca-senha/", password_reset, name="password_reset"),
    path("troca-senha/enviada/", password_reset_done, name="password_reset_done"),
    path("troca-senha/<uidb64>/<token>/", password_reset_confirm, name="password_reset_confirm",),
    path("troca-senha/atualizada/", password_reset_complete, name="password_reset_complete",),
    path(
        "ativar/sucesso/",
        TemplateView.as_view(template_name="brasilio_auth/activation_complete.html"),
        name="activation_complete",
    ),
    path("ativar/<str:activation_key>/", views.ActivationView.as_view(), name="activate_user",),
    path("entrar/", disable_non_logged_user_cache(views.RegistrationView.as_view()), name="sign_up",),
    path(
        "entrar/sucesso/",
        TemplateView.as_view(template_name="brasilio_auth/registration_complete.html"),
        name="sign_up_complete",
    ),
    path(
        "entrar/fechado/",
        TemplateView.as_view(template_name="brasilio_auth/registration_closed.html"),
        name="sign_up_disallowed",
    ),
    path("tokens-api/", views.list_user_api_tokens, name="list_api_tokens"),
)
