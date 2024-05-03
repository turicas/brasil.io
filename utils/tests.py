from django.conf import settings


class DjangoAssertionsMixin:
    """
    This class is a base test class to beter usage of custom assert methods
    """

    def assertTemplateUsed(self, response, template_name, *args, **kwargs):
        invalid_string = "Invalid: '%s'"
        settings.TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = invalid_string

        super().assertTemplateUsed(response, template_name, *args, **kwargs)
        assert invalid_string not in response.content.decode()
