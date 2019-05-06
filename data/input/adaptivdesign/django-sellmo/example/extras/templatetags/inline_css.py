from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles import finders
from django.conf import settings

register = template.Library()


@register.simple_tag
def inline_css(path):
    if getattr(settings, 'DEBUG', False):
        full_path = finders.find(path)
        with open(full_path, 'rb') as file:
            return file.read()
    else:
        with staticfiles_storage.open(path) as file:
            return file.read()
