from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from django.views.generic.edit import UpdateView
from django.contrib.auth.models import User
from django.urls import reverse

from brasilio_auth.forms import UserCreationForm


class CreateUserView(CreateView):
    template_name = 'brasilio_auth/user_creation_form.html'
    model = get_user_model()
    form_class = UserCreationForm
    success_url = settings.LOGIN_REDIRECT_URL

    def get_context_data(self, *args, **kwargs):
        context = super(CreateUserView, self).get_context_data()
        next = self.request.GET.get('next', None)
        if next:
            context['next'] = next
        return context

    def form_valid(self, *args, **kwargs):
        super(CreateUserView, self).form_valid(*args, **kwargs)
        login(self.request, self.object)
        url = self.request.POST.get('next', None) or self.success_url
        return redirect(url)


class ProfileUpdate(UpdateView):
    model = User
    pk_url_kwarg = 'user_id'
    fields = ['first_name', 'last_name', 'username']
    template_name = 'brasilio_auth/profile_update_form.html'
    def get_success_url(self):
        return reverse('brasilio_auth:profile_update_form', args=[self.object.id])
