#!/usr/bin/env python
# coding: utf-8

from django.views.generic.base import ContextMixin
from django.contrib import messages
from ..models import Config
from ..models import UserProfile


class BaseViewMixin(ContextMixin):

    def get_context_data(self, **kwargs):
        context = super(BaseViewMixin, self).get_context_data(**kwargs)
        if 'theme' not in context:
            try:
                profile = self.request.user.profile
            except:
                profile = UserProfile.get_sys_profile()
            opt = Config.get_user_conf(profile, 'theme')
            context['theme'] = opt.value if opt else 'simplex'
        return context

    def info(self, message, tags=''):
        messages.info(request=self.request, message=message, extra_tags=tags)

    def warn(self, message, tags=''):
        messages.warning(request=self.request, message=message, extra_tags=tags)

    def error(self, message, tags=''):
        messages.error(request=self.request, message=message, extra_tags=tags)

    def success(self, message, tags=''):
        messages.success(request=self.request, message=message, extra_tags=tags)

    def debug(self, message, tags=''):
        messages.set_level(self.request, messages.DEBUG)
        messages.debug(request=self.request, message=message, extra_tags=tags)