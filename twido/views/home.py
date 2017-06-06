#!/usr/bin/env python
# coding: utf-8
from collections import OrderedDict
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _, gettext_noop
from .base import BaseViewMixin
from ..models import SocialAccount, TaskStatus
from ..models import Task, List, SysList


from pyutils.langutil import PropertyDict, MutableEnum
# class I18N_MSGS(object):

I18N_MSGS = MutableEnum(
    # home_tasks_title_today=_('today'),
    # home_tasks_text_today=_('Come on, you are about to completed all the tasks!'),
    # home_tasks_text_today_empty=_('Cheers, you have completed all the tasks for today!'),
    # home_tasks_title_soon=_('soon'),
    # home_tasks_text_soon=_('Tasks in %d days (including those without deadline)'),
    # home_tasks_title_expired=_('expired'),
    # home_tasks_text_expired=_(
    #     'Tasks passed the deadline. Restart them or you may want to mark all these tasks "%(expire)s" or "%(cancel)s".'),

    home_tasks={
        '__today': MutableEnum(
            text=_('Come on, you are about to completed all the tasks!'),
            empty=_('Cheers, you have completed all the tasks for today!'),
        ),
        '__soon': MutableEnum(
            text=_('Tasks in %d days (including those without deadline)'),
            text_args=SysList.soon_days,
            empty='',
        ),
        '__expired': MutableEnum(
            text=_('Tasks passed the deadline. Restart them or you may want to '
                   'mark all these tasks "%(expire)s" or "%(cancel)s".'),
            text_args={'expire': TaskStatus.get_text(TaskStatus.EXPIRED),
                       'cancel': TaskStatus.get_text(TaskStatus.CANCEL)},
            empty='',
        ),
    }
)

@method_decorator(login_required, 'dispatch')
class HomeView(TemplateView, BaseViewMixin):

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        profile = self.request.user.profile
        # accs = SocialAccount.objects.filter(profile=profile).values_list('platform')

        context['lists'] = List.objects.filter(profile=profile).order_by('name')

        entries = 10
        sys_list = SysList(profile=profile)
        context['sys_lists'] = sys_list.all

        task_sets = []
        for name, lst in sys_list.all.items():
            task_set = {
                'name': lst.name,
                'title': lst.get_name,
                'text': I18N_MSGS.home_tasks[lst.name].text if 'text_args' not in I18N_MSGS.home_tasks[lst.name] else
                        I18N_MSGS.home_tasks[lst.name].text % I18N_MSGS.home_tasks[lst.name].text_args,
                'empty': I18N_MSGS.home_tasks[lst.name].empty,
                'class': '',
                'tasks': sys_list.get(lst.name).tasks[:entries]
            }
            task_sets.append(task_set)
        context['task_sets'] = task_sets

        context['tasks_fields'] = ('status', 'title', 'reminder')
        context['tasks_editables'] = ('status', 'title', 'reminder')
        context['tasks_actions'] = ('detail',)
        context['taskstatus'] = TaskStatus
        return context
