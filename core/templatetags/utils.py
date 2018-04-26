from django.template import Context, Library, Template


register = Library()

@register.filter(name='getattribute')
def getattribute(obj, attr):
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif attr in obj:
        return obj[attr]
    else:
        raise ValueError('Cannot get attribute "{}"'.format(attr))


@register.filter(name='render')
def render(template_text, obj):
    return Template(template_text).render(
        Context(obj.__dict__, use_l10n=False)
    )
