from covid19.permissions import user_has_covid19_permissions


def is_covid19_contributor(request):
    user = getattr(request, "user", None)
    is_contributor = False

    if user and user.is_authenticated:
        is_contributor = user.is_superuser or (user.is_staff and user_has_covid19_permissions(user))

    return {"is_covid19_contributor": is_contributor}
