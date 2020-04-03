from django.utils.module_loading import import_string
from markdownx import settings as mdx_settings
from django import template

register = template.Library()

@register.filter
def markdownify(text):
    markdown_func = import_string(
        mdx_settings.MARKDOWNX_MARKDOWNIFY_FUNCTION
    )  # Gets value from markdownx settings because it can return a default.
    return markdown_func(text)
