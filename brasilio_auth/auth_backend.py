from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, *args, **kwargs):
        if username is None:
            return None
        elif "@" in username:
            # Won't allow anybody having "@" in username to log in
            query = Q(email=username)
        else:
            query = Q(username=username)

        try:
            user = User.objects.get(query)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        else:
            return None
