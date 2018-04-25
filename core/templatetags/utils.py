from django import template


register = template.Library()

@register.filter(name='getattribute')
def getattribute(obj, attr):
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif attr in obj:
        return obj[attr]
    else:
        raise ValueError('Cannot get attribute "{}"'.format(attr))


@register.filter(name='is_digit')
def is_digit(value):
    return str(value).isdigit()
