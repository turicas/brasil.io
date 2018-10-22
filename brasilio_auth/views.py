from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.urls import reverse
from django.views.generic.edit import CreateView
from django.shortcuts import redirect

from brasilio_auth.forms import UserCreationForm


class CreateUserView(CreateView):
    template_name = 'brasilio_auth/user_creation_form.html'
    model = get_user_model()
    form_class = UserCreationForm
    success_url = settings.LOGIN_REDIRECT_URL

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_anonymous:
            next = self.request.GET.get('next', None)
            if next:
                return redirect(next)
            return redirect(reverse('core:home'))
        return super().dispatch(request, *args, **kwargs)


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
