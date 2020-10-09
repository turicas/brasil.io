from django.conf import settings


class DjangoAssertionsMixin:
    """
    This class is a base test class to beter usage of custom assert methods
    """

    def assertTemplateUsed(self, response, template_name, *args, **kwargs):
        super().assertTemplateUsed(response, template_name, *args, **kwargs)
        assert settings.TEMPLATE_STRING_IF_INVALID not in response.content.decode()
