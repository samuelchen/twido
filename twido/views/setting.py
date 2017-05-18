#!/usr/bin/env python
# coding: utf-8
from bootstrap_themes import list_themes
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from ..models import SocialPlatform, SocialAccount, Config
from .base import BaseViewMixin

import logging
log = logging.getLogger(__name__)


@method_decorator(login_required, 'dispatch')
class SettingView(TemplateView, BaseViewMixin):

    def get_context_data(self, **kwargs):
        context = super(SettingView, self).get_context_data(**kwargs)
        p = self.request.user.profile
        context['profile'] = p

        # TODO: optimization required
        # context['x'] = sorted(Config.objects.filter(profile=p).values('name', 'value'), key=lambda x:x['name'])
        conf = {}
        for opt in Config.objects.filter(profile=p):
            conf[opt.name] = opt
        context['conf'] = conf

        # social account linking
        context['social_platforms'] = SocialPlatform
        social_accounts = {}
        for acc in SocialAccount.objects.filter(profile=p).iterator():
            social_accounts[acc.platform] = acc
        context['social_accounts'] = social_accounts
        # print(social_accounts)

        context['themes'] = list_themes()

        return context

    def post(self, request, *args, **kwargs):
        # ONLY ajax call

        profile = self.request.user.profile

        # TODO: clean/escape data (better use Django form for field validation)
        req = request.POST

        # config setting request
        name = req.get('name', None)
        value = req.get('value', None)

        if name and value:
            Config.set_user_conf(profile=profile, name=name, value=value)

        return HttpResponse('')