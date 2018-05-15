from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.views.generic.edit import CreateView
from django.shortcuts import redirect

from brasilio_auth.forms import UserCreationForm


class CreateUserView(CreateView):
    template_name = 'brasilio_auth/user_creation_form.html'
    model = get_user_model()
    form_class = UserCreationForm
    success_url = settings.LOGIN_REDIRECT_URL

    def form_valid(self, *args, **kwargs):
        super(CreateUserView, self).form_valid(*args, **kwargs)
        login(self.request, self.object)
        return redirect(self.success_url)
