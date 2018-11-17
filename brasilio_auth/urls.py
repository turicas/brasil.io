from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.urls import path

from brasilio_auth.views import CreateUserView, ProfileUpdate


views_config = {
    'login': auth_views.LoginView.as_view(template_name='brasilio_auth/login.html'),
    'logout': auth_views.LogoutView.as_view(),
    'password_reset': auth_views.PasswordResetView.as_view(
        template_name='brasilio_auth/password_reset.html',
        success_url=reverse_lazy('brasilio_auth:password_reset_done'),
        email_template_name='brasilio_auth/emails/password_reset_email.html',
        subject_template_name='brasilio_auth/emails/password_reset_subject.txt',
    ),
    'password_reset_done': auth_views.PasswordResetDoneView.as_view(
        template_name='brasilio_auth/password_reset_done.html',
    ),
    'password_reset_confirm': auth_views.PasswordResetConfirmView.as_view(
        template_name='brasilio_auth/password_reset_form.html',
        success_url=reverse_lazy('brasilio_auth:password_reset_complete'),
    ),
    'password_reset_complete': auth_views.PasswordResetCompleteView.as_view(
        template_name='brasilio_auth/password_reset_complete.html',
    ),
}

app_name = 'brasilio_auth'
urlpatterns = (
    path('login/', views_config['login'], name='login'),
    path('logout/', views_config['logout'], name='logout'),
    path('troca-senha/', views_config['password_reset'], name='password_reset'),
    path('troca-senha/enviada/', views_config['password_reset_done'], name='password_reset_done'),
    path('troca-senha/<uidb64>/<token>/', views_config['password_reset_confirm'], name='password_reset_confirm'),
    path('troca-senha/atualizada/', views_config['password_reset_complete'], name='password_reset_complete'),
    path('logout/', views_config['logout'], name='logout'),
    path('entrar/', CreateUserView.as_view(), name='sign_up'),
    path('editar-perfil/<int:user_id>', ProfileUpdate.as_view(), name='profile_update_form')
)
