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
from twido.views import paginate

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

        p = self.request.GET.get('p', 1)   # current page
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

        tasks = Task.objects.filter(visibility=Visibility.PUBLIC)
        if settings.DEBUG:
            tasks = tasks.filter(meta__timex__contains='TIMEX3')
        tasks = paginate(tasks.order_by('-created_at'), cur_page=p, entries_per_page=10)
        context['page'] = context['tasks'] = tasks

        if settings.DEBUG:
            context['code_css'] = Timex3Parser.get_highlight_css()
        return context
