import os
import re

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


@register.filter
def is_url(string):
    return re.search('^http', string)


@register.filter
def is_list(value):
    return isinstance(value, list)


@register.filter
def is_dict(value):
    return isinstance(value, dict)


@register.filter
def is_string(value):
    return isinstance(value, str)


@register.filter
@stringfilter
def replace(value, arg):
    args = arg.split(",")
    return value.replace(args[0], args[1])
