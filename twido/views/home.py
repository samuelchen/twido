#!/usr/bin/env python
# coding: utf-8
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from .base import BaseViewMixin
from ..models import SocialAccount, TaskStatus
from ..models import Task, List


from pyutils.langutil import PropertyDict, MutableEnum
# class I18N_MSGS(object):
I18N_MSGS = MutableEnum(
    home_tasks_title_today=_('today'),
    home_tasks_text_today=_('Come on, you are about to completed all the tasks!'),
    home_tasks_text_today_empty=_('Cheers, you have completed all the tasks for today!'),
    home_tasks_title_soon=_('soon'),
    home_tasks_text_soon=_('Tasks in %d days (including those without deadline)'),
    home_tasks_title_expired=_('expired'),
    home_tasks_text_expired=_(
        'Tasks passed the deadline. Restart them or you may want to mark all these tasks "%(expire)s" or "%(cancel)s".'),
)

@method_decorator(login_required, 'dispatch')
class HomeView(TemplateView, BaseViewMixin):

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        profile = self.request.user.profile
        accs = SocialAccount.objects.filter(profile=profile).values_list('platform')

        context['lists'] = List.objects.filter(profile=profile).all()

        soon_days = 3
        entries = 10
        now = timezone.now()
        today = timezone.datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        tomorrow = today + timedelta(days=1)
        context['task_sets'] = [
            {'title': I18N_MSGS.home_tasks_title_today,
             'text': I18N_MSGS.home_tasks_text_today,
             'empty': I18N_MSGS.home_tasks_text_today_empty,
             'class': '',
             'tasks': Task.objects.filter(profile=profile, reminder__range=(today, tomorrow))[:entries]},
            {'title': I18N_MSGS.home_tasks_title_soon,
             'text': I18N_MSGS.home_tasks_text_soon % soon_days,
             'empty': '',
             'class': '',
             'tasks': Task.objects.filter(profile=profile).filter(
                 Q(reminder__lt=timezone.now() - timedelta(days=soon_days)) | Q(reminder=None))[:entries]},
            {'title': I18N_MSGS.home_tasks_title_expired,
             'text': I18N_MSGS.home_tasks_text_expired % {'expire': TaskStatus.get_text(TaskStatus.EXPIRED),
                                                          'cancel': TaskStatus.get_text(TaskStatus.CANCEL)
                                                          },
             'empty': '',
             'class': '',
             'tasks': Task.objects.filter(profile=profile, reminder__lt=timezone.now()).exclude(
                 status__in=(TaskStatus.DONE, TaskStatus.CANCEL))[:entries]},
        ]

        context['tasks_fields'] = ('status', 'title', 'reminder')
        context['tasks_editables'] = ('status', 'title', 'reminder')
        context['tasks_actions'] = ('detail',)
        context['taskstatus'] = TaskStatus
        return context
