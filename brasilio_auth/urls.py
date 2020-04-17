from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from brasilio_auth.views import CreateUserView


login = auth_views.LoginView.as_view(template_name="brasilio_auth/login.html")
logout = auth_views.LogoutView.as_view()

password_reset = auth_views.PasswordResetView.as_view(
    template_name="brasilio_auth/password_reset.html",
    success_url=reverse_lazy("brasilio_auth:password_reset_done"),
    email_template_name="brasilio_auth/emails/password_reset_email.html",
    subject_template_name="brasilio_auth/emails/password_reset_subject.txt",
)
password_reset_done = auth_views.PasswordResetDoneView.as_view(
    template_name="brasilio_auth/password_reset_done.html"
)
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
    path(
        "troca-senha/<uidb64>/<token>/",
        password_reset_confirm,
        name="password_reset_confirm",
    ),
    path(
        "troca-senha/atualizada/",
        password_reset_complete,
        name="password_reset_complete",
    ),
    path("logout/", logout, name="logout"),
    path("entrar/", CreateUserView.as_view(), name="sign_up"),
)
