#!/usr/bin/env python
# coding: utf-8
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.utils.translation import ugettext as _
from django.conf.global_settings import LANGUAGES as ALL_LANGUAGES
from ..models import UserProfile, SocialPlatform, SocialAccount
from .base import BaseViewMixin

import logging
log = logging.getLogger(__name__)


class I18N_MSGS(object):
    profile_saved_success = _('Profile is saved successfully.'),
    redirect_to_home = _('Will redirect to home page...<br>'
                         'If not start, please <a href="%s">click me to Home page</a>.')


@method_decorator(login_required, 'dispatch')
class ProfileView(TemplateView, BaseViewMixin):

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['profile'] = self.request.user.profile
        context['ALL_LANGUAGES'] = ALL_LANGUAGES
        return context

    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile = user.profile

        url_home = reverse('home')
        if profile.timestamp - profile.created_at < timedelta(minutes=1):
            kwargs['redirect'] = url_home

        # TODO: clean/escape data (better use Django form for field validation)
        req = request.POST
        profile.username = req.get('username', profile.username)
        profile.name = req.get('name', profile.name)
        gender = req.get('gender', profile.gender)
        profile.gender = bool(gender)
        profile.timezone = req.get('timezone', profile.timezone)
        profile.location = req.get('location', profile.location)
        profile.lang = req.get('lang', profile.lang)
        profile.img_url = req.get('img_url', profile.img_url)

        profile.save()

        self.success(I18N_MSGS.profile_saved_success)
        if 'redirect' in kwargs:
            self.success(I18N_MSGS.redirect_to_home % url_home)

        return self.get(request, *args, **kwargs)


#TODO: temp json view
@method_decorator(login_required, 'dispatch')
class ProfileUsernamesJsonView(View, BaseViewMixin):

    def get(self, request, *args, **kwargs):
        log.debug('%s %s' % (request, request.POST))

        q = request.GET.get('q', '')
        p = int(request.GET.get('p', 1))

        # page = paginate(query, cur_page=p, entries_per_page=30)

        # TODO: use ElasticSearch to optimize. DO not query database.
        query = UserProfile.objects.exclude(username=UserProfile.get_sys_profile_username())\
            .filter(Q(username__contains=q) | Q(name__contains=q))
        query1 = SocialAccount.objects.filter(Q(account__contains=q))

        usernames = []
        for rec in query.values_list('username', 'name'):
            usernames.append({
                "id": rec[0],
                "text": rec[1] + ' (' + rec[0] + ')' if rec[1] else rec[0]
            })

        for rec in query1.values_list('account', 'name', 'platform'):
            usernames.append({
                "id": '[' + rec[2] + ']' + rec[0],
                "text": SocialPlatform.get_text(rec[2]) + ':' + (rec[1] + ' (' + rec[0] + ')' if rec[1] and rec[1] != rec[0] else rec[0])
            })
        return JsonResponse(usernames, safe=False)




