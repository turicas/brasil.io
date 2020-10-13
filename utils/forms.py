from captcha.fields import ReCaptchaField
from django.conf import settings


class FlagedReCaptchaField(ReCaptchaField):
    def validate(self, *args, **kwargs):
        if settings.DISABLE_RECAPTCHA:
            self.validators = []
            self.required = False
        else:
            super().validate(*args, **kwargs)
