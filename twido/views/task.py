#!/usr/bin/env python
# coding: utf-8
from django.conf import settings

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from ..models import Task, List, TaskStatus, Visibility
from .base import BaseViewMixin
from .common import paginate
from ..parser import Timex3Parser

import logging
log = logging.getLogger(__name__)


class I18N_MSGS(object):

    primary_key_is_none = _('Primary key is None')
    prop_cannot_be = _('"%(prop)s" can not be "%(value)s"')

    task_new_name = _('New Task')
    task_created = _('New task created.')

    resp_invalid_action = _('Invalid request. (action=%s)')


class TaskView(TemplateView, BaseViewMixin):

    def get_task_model(self):
        return Task

    def get_list_model(self):
        return List

    def get_view_name(self):
        return 'task'

    def get_context_data(self, **kwargs):
        context = super(TaskView, self).get_context_data(**kwargs)
        TaskModel = self.get_task_model()

        profile = self.request.user.profile
        p = self.request.GET.get('p', None)   # current page

        pk = context['pk']
        if 'thetask' not in context:
            task = get_object_or_404(TaskModel, profile=profile, id=pk)

            if settings.DEBUG:
                context['code_css'] = Timex3Parser.get_highlight_css()
                # task = Timex3Parser.parse_task(task, include_code=True)

            context['thetask'] = task
            context['thelist'] = task.list

        if 'page' not in context:
            # context['page'] = paginate(TaskModel.objects.filter(profile=profile, list=task.list), cur_page=p, entries_per_page=10)
            context['page'] = TaskModel.objects.filter(profile=profile, list=task.list)

        if 'taskstatus' not in context:
            context['taskstatus'] = TaskStatus

        # variables for tasks.html includes
        # context['tasks_fields'] = ('status', 'title', 'due')
        # context['tasks_editables'] = ('status', 'title', 'due', 'labels')
        # context['tasks_actions'] = ('detail', 'del')

        if 'visibility' not in context:
            context['visibility'] = Visibility

        return context

    def post(self, request, pk, *args, **kwargs):
        # AJAX
        # TODO: move to rest api

        TaskModel = self.get_task_model()

        req = request.POST
        profile = request.user.profile
        action = req.get('action', None)
        log.debug('task view action: %s' % action)

        log.debug('task view pk: %s' % pk)

        if action is not None:
            # HTTP response for form.submit

            if action == 'add-task':
                # add a task
                list_id = req.get('list_id', self.get_list_model().get_default(profile).id)
                task = TaskModel.objects.create(profile=profile, list_id=list_id, title=I18N_MSGS.task_new_name)
                self.info(I18N_MSGS.task_created)
                return redirect(self.get_view_name(), pk=task.id)
            elif action == 'del-task':
                task = get_object_or_404(TaskModel, profile=profile, id=pk)
                lst = task.list
                log_str = 'Task "%s" deleted by %s' % (task, profile)
                task.delete()
                log.info(log_str)

                if lst.task_set.count() <= 0:
                    return redirect('list', pk=lst.id)
                else:
                    return redirect(self.get_view_name(), pk=lst.task_set.first().id)
            else:
                log.warn('Invalid request. (action=%s)' % action)
                if request.is_ajax():
                    return HttpResponseBadRequest(I18N_MSGS.resp_invalid_action % action)
                else:
                    self.error(I18N_MSGS.resp_invalid_action % action)

        name = req.get('name', None)
        if pk is not None and name is not None:
            pk = int(pk)

            value = req.get('value', None)
            if name == 'labels':
                value = ','.join(req.getlist('value[]', []))
            if value is not None and value.strip() == '':
                value = None
            elif name == 'status' or name == 'visibility':
                value = int(value)
            # print(name, '-', value)
            try:
                task = TaskModel.objects.get(id=pk)
                setattr(task, name, value)
                task.save(update_fields=[name, ])
            except Exception as err:
                log.exception(err)
                return HttpResponseBadRequest(I18N_MSGS.prop_cannot_be % {'prop': name, 'value': value})

            data = {
                'status_icon_class': task.get_status_icon(),
                'status_text': task.get_status_text(),
                'visibility_icon_class': task.get_visibility_icon(),
                'visibility_text': task.get_visibility_text(),
                'name': name,
                'value': value
            }
            return JsonResponse(data)
        else:
            return HttpResponseBadRequest(I18N_MSGS.primary_key_is_none)
