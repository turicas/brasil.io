from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from brasilio_auth.validators import normalize_email_address

User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, *args, **kwargs):
        if username is None:
            return None
        username = username.strip()
        if "@" in username:
            # Há centenas de contas antigas com o MESMO e-mail (a unicidade no cadastro só existe desde 2020) e outras
            # que colidem apenas no normalizado. Testa a senha em cada candidata, e-mail exato antes do alias.
            candidatas = list(User.objects.filter(email__iexact=username).order_by("id"))
            pks_exatos = {user.pk for user in candidatas}
            candidatas += [
                user
                for user in User.objects.filter(normalized_email__value=normalize_email_address(username))
                if user.pk not in pks_exatos
            ]
        else:
            # `username` é único no banco, mas com distinção de maiúsculas: `larraw` e `Larraw` coexistem.
            candidatas = User.objects.filter(username__iexact=username).order_by("id")

        for user in candidatas:
            if user.check_password(password):
                return user
        return None
