from django.contrib.auth import views as auth_views
from django.urls import path


views_config = {
    'login': auth_views.LoginView.as_view(template_name='brasilio_auth/login.html'),
    'logout': auth_views.LogoutView.as_view(),
    'password_reset': auth_views.PasswordResetView.as_view(
        template_name='brasilio_auth/password_reset.html',
        success_url='/auth/troca-senha/enviada/',
    ),
    'password_reset_done': auth_views.PasswordResetDoneView.as_view(
        template_name='brasilio_auth/password_reset_done.html',
    ),
}

app_name = 'brasilio_auth'
urlpatterns = (
    path('login/', views_config['login'], name='login'),
    path('logout/', views_config['logout'], name='logout'),
    path('troca-senha/', views_config['password_reset'], name='password_reset'),
    path('troca-senha/enviada/', views_config['password_reset_done'], name='password_reset_done'),
)
