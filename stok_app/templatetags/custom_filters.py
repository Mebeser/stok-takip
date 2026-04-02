from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """ Django Template içinde çarpma işlemi yapmak için. """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
