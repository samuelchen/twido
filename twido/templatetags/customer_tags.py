#!/usr/bin/env python
# coding: utf-8

"""
customer tags for template
"""

from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import re

register = Library()


@stringfilter
@register.filter(needs_autoescape=True)
def spacify(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub('\s', '&' + 'nbsp;', esc(value)))


@stringfilter
@register.filter
def _2space(value):
    """
    Convert underscores to spaces for a string.
    :param value:
    :return:
    """
    return value.replace('_', ' ')


@stringfilter
@register.filter
def space2_(value):
    """
    Convert spaces to underscores for a string.
    :param value:
    :return:
    """
    return value.replace(' ', '_')


@register.simple_tag
def key_from_var(obj, *args):
    """
    Obtain values from dict/object with given key variables in template.
    e.g.
    If you want to render user.name.first_name in Django template,
    Use {% key_from_var user name first_name %}
    :param obj:
    :param args:
    :return:
    """
    val = obj
    for key in args:
        if key in val:
            val = val[key]
        elif hasattr(val, key):
            val = getattr(val, key)
        else:
            return ''
    return val


@register.filter
@stringfilter
def trim(value):
    return value.strip()


# re_isurl = re.compile(r"(?isu)(http[s]\://[a-zA-Z0-9\.\?/&\=\:]+)")
re_isurl = re.compile(r"(?isu)(http[s]\://[a-zA-Z0-9\.\?/&\=\:\-_]+)")
@register.filter
@stringfilter
def url2link(value):
    """
    Replace URLs in value to LINKs.
    e.g.
    value = "Please go to http://www.google.com to search."
    retuns: "Please go to <a href="http://www.google.com">http://www.google.com</a> to search."
    :param value:
    :return:
    """
    return re_isurl.sub(lambda m: '<a href="%s">%s</a>' % (m.group(0), m.group(0)), value)


# re_ishash = re.compile(r"(?ish)(\w[#todo|#wish]\w)")
# @register.filter
# @stringfilter
# def hash2link(value):
#     """
#     Replace URLs in value to LINKs.
#     e.g.
#     value = "Buy a pen tomorrow #todo."
#     retuns: "Buy a pen tomorrow <a href="#">#todo</a>."
#     :param value:
#     :return:
#     """
#     return re_ishash.sub(lambda m: '<a href="/hash/%s">%s</a>' % (m.group(0), m.group(0)), value)