#!/usr/bin/env python
# coding: utf-8
from django.conf import settings
from django.db.models import Q

from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from ..models import UserProfile, Visibility
from ..models import SocialAccount
from ..models import Task, List
from .base import BaseViewMixin
from pyutils.langutil import MutableEnum

import dateparser

from pygments.lexers.html import XmlLexer
from pygments.formatters.html import HtmlFormatter
from pygments import highlight
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import logging
log = logging.getLogger(__name__)


class IndexView(TemplateView, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        # if settings.DEBUG:
        #     host = request.get_host()
        #     if host.startswith('fonts.googleapis.com'):
        #         return HttpResponseRedirect("/gf/")

        # if request.user.is_authenticated:
        #     return HttpResponseRedirect("/home")
        # else:
        return super(IndexView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        sys_profile = UserProfile.get_sys_profile()
        profile_max = 10
        context['profiles'] = UserProfile.objects.exclude(
            Q(user=None) | Q(email__contains=UserProfile.get_temp_email_suffix()) |
            Q(email__contains=UserProfile.get_local_email_suffix())
        ).order_by('-id')[:profile_max]
        social_account_max = profile_max - len(context['profiles'])
        context['social_accounts'] = SocialAccount.objects.filter(
            Q(profile=sys_profile) | Q(profile__email__contains=UserProfile.get_temp_email_suffix())
        ).order_by('-id')[:social_account_max]

        context['tasks'] = Task.objects.filter(visibility=Visibility.PUBLIC).order_by('-created_at')[:10]
        if settings.DEBUG:
            tasks, css = self._highlight(context['tasks'])
            context['css'] = css

        return context

    def _highlight(self, tasks):

        formatter = HtmlFormatter(encoding='utf-8', nowrap=False, style='emacs', linenos=False)
        lexer = XmlLexer()

        for task in tasks:

            task.dates = []
            task.code = None

            if not task.content:
                continue

            task.code = highlight(task.content, lexer, formatter)
            # print(task.title)
            xml = ET.fromstring(task.content)
            for node in xml.findall("./TEXT/TIMEX3"):
                dt = MutableEnum()
                dt.text = node.text
                # print(node.text)
                for k, v in node.items():
                    # print('  ', k, v)
                    dt[k] = v
                if dt.type == 'DATE' and dt.text:
                    try:
                        dt.v = dateparser.parse(dt.text)
                        # dt.v = parse_datetime(dt.text)
                    except Exception as err:
                        log.warn(err)
                        dt.v = None
                task.dates.append(dt)

        return tasks, formatter.get_style_defs()