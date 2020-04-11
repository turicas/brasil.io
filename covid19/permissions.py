from django.conf import settings


def user_has_state_permission(user, uf):
    perm_code = 'covid19.' + settings.COVID_IMPORT_PERMISSION_PREFIX + uf.upper()
    return user.has_perm(perm_code)
