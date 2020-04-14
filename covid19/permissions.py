from localflavor.br.br_states import STATE_CHOICES

from django.conf import settings


def _format_perm_code(uf):
    return 'covid19.' + settings.COVID_IMPORT_PERMISSION_PREFIX + uf.upper()


def user_has_state_permission(user, uf):
    return user.has_perm(_format_perm_code(uf))


def user_has_covid19_permissions(user):
    permissions = set()
    for uf, state in STATE_CHOICES:
        permissions.add(_format_perm_code(uf))
    return bool(user.get_all_permissions() & permissions)
