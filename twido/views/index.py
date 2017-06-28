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
from ..parser import Timex3Parser

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

        tasks = []
        context['tasks'] = Task.objects.filter(visibility=Visibility.PUBLIC).order_by('-created_at')[:10]
        if settings.DEBUG:
            for task in context['tasks']:
                Timex3Parser.parse_task(include_code=True)
                tasks.append(task)
            context['tasks'] = tasks
            context['code_css'] = Timex3Parser.get_highlight_css()
        return context
