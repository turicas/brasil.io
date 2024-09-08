from django.conf import settings


def template_settings(request):
    return {
        "ENV_TYPE": settings.ENV_TYPE,
        "EMAIL_SUBJECT_PREFIX": settings.EMAIL_SUBJECT_PREFIX,
    }
