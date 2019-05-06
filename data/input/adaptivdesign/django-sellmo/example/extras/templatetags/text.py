from django import template
from django.utils.text import normalize_newlines


register = template.Library()


@register.filter("split_linebreaks")
def split_linebreaks(value):
    value = normalize_newlines(value)
    return value.split('\n')
