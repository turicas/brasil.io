from django.contrib.auth import views as auth_views
from django.urls import path


views_config = {
    'login': auth_views.LoginView.as_view(template_name='brasilio_auth/login.html'),
}

app_name = 'brasilio_auth'
urlpatterns = (
    path('login/', views_config['login'], name='login'),
)
