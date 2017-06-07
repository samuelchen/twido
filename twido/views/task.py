#!/usr/bin/env python
# coding: utf-8

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from ..models import Task,  TaskStatus
from .base import BaseViewMixin
from .common import paginate

import logging
log = logging.getLogger(__name__)


class I18N_MSGS(object):

    primary_key_is_none = _('Primary key is None')
    prop_cannot_be = _('"%(prop)s" can not be "%(value)s"')


class TaskView(TemplateView, BaseViewMixin):

    def get_task_model(self):
        return Task

    def get_context_data(self, **kwargs):
        context = super(TaskView, self).get_context_data(**kwargs)
        TaskModel = self.get_task_model()

        profile = self.request.user.profile
        p = self.request.GET.get('p', None)   # current page

        pk = context['pk']
        task = get_object_or_404(TaskModel, profile=profile, id=pk)
        context['thetask'] = task

        if 'page' not in context:
            context['page'] = paginate(TaskModel.objects.filter(profile=profile, list=task.list), cur_page=p, entries_per_page=10)

        if 'taskstatus' not in context:
            context['taskstatus'] = TaskStatus

        # variables for tasks.html includes
        # context['tasks_fields'] = ('status', 'title', 'due', 'labels')
        # context['tasks_editables'] = ('status', 'title', 'due', 'labels')
        # context['tasks_actions'] = ('detail', 'del')

        return context

    def post(self, request, pk, *args, **kwargs):
        # AJAX
        # TODO: move to rest api
        req = request.POST

        TaskModel = self.get_task_model()

        if pk is not None:
            pk = int(pk)
            name = req.get('name', None)
            value = req.get('value', None)

            if name == 'labels':
                value = ','.join(req.getlist('value[]', []))
            if value is not None and value.strip() == '':
                value = None
            elif name == 'status':
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
                'status_icon_class': task.get_status_glyphicon(),
                'status_text': task.get_status_text(),
                'name': name,
                'value': value
            }
            return JsonResponse(data)
        else:
            return HttpResponseBadRequest(I18N_MSGS.primary_key_is_none)
