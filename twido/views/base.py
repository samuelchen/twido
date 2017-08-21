#!/usr/bin/env python
# coding: utf-8
from django.db.models import Q
from django.views.generic.base import ContextMixin
from django.contrib import messages
from django.utils import translation
from django.conf import settings
from django.utils import timezone

from ..models import Config
from ..models import UserProfile
from ..models import Task, TaskStatus


class BaseViewMixin(ContextMixin):

    def get_context_data(self, **kwargs):
        context = super(BaseViewMixin, self).get_context_data(**kwargs)

        profile = self.get_profile()

        if 'theme' not in context:
            opt = Config.get_user_conf(profile, 'theme')
            context['theme'] = opt.value if opt else 'simplex'

        if not profile.is_faked and 'LANGUAGE_CODE' not in context:
            # only set for REAL users (they have lang setting)
            opt = Config.get_user_conf(profile, 'lang')
            if opt:
                # only set if user configured language in setting.
                # otherwise, use middleware detected.
                context['LANGUAGE_CODE'] = opt.value
                translation.activate(context['LANGUAGE_CODE'])

        # if 'view_size' not in context:
        #     opt = Config.get_user_conf(profile, 'view_size')
        #     context['view_size'] = opt.value if opt else 'G'

        if 'website' not in context:
            context['website'] = {
                'name': settings.WEBSITE_NAME
            }

        if 'expiring_tasks' not in context:
            context['expiring_tasks'] = self.get_expiring_tasks()

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

    def get_profile(self):
        if self.request.user.is_anonymous:
            profile = UserProfile.get_sys_profile()
        else:
            profile = self.request.user.profile
        return profile

    def get_expiring_tasks(self, hours=3, days=0):
        profile = self.get_profile()
        start = timezone.now()
        end = start + timezone.timedelta(days=days, hours=hours)
        tasks = Task.objects.filter(profile=profile, due__gte=start, due__lte=end).filter(
            ~Q(status=TaskStatus.CANCEL) & ~Q(status=TaskStatus.DONE)).order_by('due')
        return tasks