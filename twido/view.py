#!/usr/bin/env python
# coding: utf-8

"""
views
"""

from django.conf import settings
from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import TemplateView
from .models import RawStatus
from .models import Todo, UserProfile
from pyutils.langutil import MutableEnum
from .utils import parse_datetime

import dateparser

from datetime import datetime, timedelta

from pygments.lexers.html import XmlLexer
from pygments.formatters.html import HtmlFormatter
from pygments import highlight
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


import logging
log = logging.getLogger(__name__)


# to render full template path
def t(template):
    return 'twido/' + template


# test view for some test purpose
if __debug__ and settings.DEBUG:
    def test(request):
        return render(request, t('test.html'))


class IndexView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        context['todos'] = Todo.objects.all()[:10]
        delta = timedelta(days=7)
        dt = datetime.utcnow() - delta
        context['profiles'] = UserProfile.objects.filter(user__date_joined__gt=dt).order_by('-user__date_joined')[:5]
        # context['profiles'] = UserProfile.objects.all()[:5]


        formatter = HtmlFormatter(encoding='utf-8', style='emacs', linenos=True)
        lexer = XmlLexer()
        for task in context['todos']:
            task.text = highlight(task.content, lexer, formatter)

            print(task.title)
            xml = ET.fromstring(task.content)
            task.dates = []
            for node in xml.findall("./TEXT/TIMEX3"):
                dt = MutableEnum()
                dt.text = node.text
                print(node.text)
                for k,v in node.items():
                    print('  ', k, v)
                    dt[k] = v
                if dt.type == 'DATE' and dt.text:
                    try:
                        dt.v = dateparser.parse(dt.text)
                        # dt.v = parse_datetime(dt.text)
                    except Exception as err:
                        log.warn(err)
                        dt.v = None
                task.dates.append(dt)
        context['css'] = formatter.get_style_defs()

        return context


@require_http_methods(['GET', ])
def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = 'authoried'
    elif request.user.is_staff:
        context['user'] = 'staff'
    else:
        context['user'] = 'forbiden'
    # context = {
    #     # "setting_keys": models.SETTING_NAMES,
    # }
    return render(request, t('index.html'), context=context)

@require_http_methods(['GET', ])
def test(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = 'authoried'
    elif request.user.is_staff:
        context['user'] = 'staff'
    else:
        context['user'] = 'forbiden'
    # context = {
    #     # "setting_keys": models.SETTING_NAMES,
    # }
    return render(request, t('test.html'), context=context)