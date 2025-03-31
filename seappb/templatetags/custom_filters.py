# custom_filters.py
from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


@register.filter
def get_attribute(obj, attr):
    """Filtro para acessar atributos de um objeto dinamicamente."""
    try:
        return getattr(obj, attr)
    except AttributeError:
        return ''