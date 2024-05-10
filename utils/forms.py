from django.conf import settings
from django_recaptcha.fields import ReCaptchaField


class FlaggedReCaptchaField(ReCaptchaField):
    def validate(self, *args, **kwargs):
        if settings.DISABLE_RECAPTCHA:
            self.validators = []
            self.required = False
        else:
            super().validate(*args, **kwargs)
