import os

from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


# See dirname(1)
@register.filter
@stringfilter
def dirname(path):
    dirname, _ = os.path.split(path)
    return dirname


# See basename(1)
@register.filter
@stringfilter
def basename(path):
    _, basename = os.path.split(path)
    return basename
