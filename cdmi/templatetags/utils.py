import os
import re

from django import template
from django.template.defaultfilters import stringfilter

from isodate import parse_duration
from isodate.isoerror import ISO8601Error


register = template.Library()


# See dirname(1)
@register.filter
@stringfilter
def dirname(path):
    dirname, _ = os.path.split(path.rstrip('/'))
    return dirname


# See basename(1)
@register.filter
@stringfilter
def basename(path):
    _, basename = os.path.split(path.rstrip('/'))
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


@register.filter
@stringfilter
def isoduration(value):
    try:
        duration = parse_duration(value)
    except ISO8601Error:
        return None
    else:
        duration = "{}".format(duration)
        duration = duration.replace(", 0:00:00", "")
        return duration
