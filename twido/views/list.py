#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from ..models import Task,  List, TaskStatus
from .base import BaseViewMixin
from .common import paginate

import logging
log = logging.getLogger(__name__)


class I18N_MSGS(object):
    # HTTP Bad Responses
    resp_invalid_action = _('Invalid request. (action=%s)')

    # UI List messages
    list_new_name = _('New List')
    list_default_cannot_delete = _('Default list can not be deleted.')
    list_created = _('New list is created.')
    list_deleted = _('List "%s" was deleted.')

    # UI task messages
    task_new_name = _('New Task')

    # model
    prop_cannot_change = _('"%s" can not be changed.')


@method_decorator(login_required, name='dispatch')
class ListView(TemplateView, BaseViewMixin):

    def get_list_model(self):
        return List

    def get_task_model(self):
        return Task

    def get_view_name(self, pk=None):
        return 'list'

    def get_context_data(self, **kwargs):

        context = super(ListView, self).get_context_data(**kwargs)
        ListModel = self.get_list_model()
        TaskModel = self.get_task_model()

        profile = self.request.user.profile
        p = self.request.GET.get('p', 1)   # current page

        if 'pk' in context:
            pk = context['pk']
            thelist = get_object_or_404(ListModel, profile=profile, id=pk)
        else:
            thelist = ListModel.get_default(profile)

        context['thelist'] = thelist
        context['p'] = p
        context['page'] = paginate(TaskModel.objects.filter(profile=profile, list=thelist).select_related('list'),
                                   cur_page=p, entries_per_page=10)
        context['lists'] = ListModel.objects.filter(profile=profile).all()

        # variables for tasks.html includes
        context['taskstatus'] = TaskStatus
        # context['tasks_fields'] = ('status', 'title', 'reminder', 'labels')
        context['tasks_editables'] = ('status', 'title', 'reminder', 'labels')
        context['tasks_actions'] = ('detail', 'del')
        context['tasks_empty_well'] = True

        return context

    def post(self, request, *args, **kwargs):
        # AJAX
        # TODO: move to rest api

        ListModel = self.get_list_model()
        TaskModel = self.get_task_model()
        req = request.POST
        # print(req)

        profile = request.user.profile
        action = req.get('action', None)

        if 'pk' in kwargs:
            pk = kwargs['pk']
        else:
            pk = ListModel.get_default(profile).id

        if action is not None:
            # HTTP response for form.submit
            if action == 'add':
                # add a list
                lst = ListModel.objects.create(profile=profile,
                                               name=(I18N_MSGS.list_new_name + ' ' + str(ListModel.objects.last().id)))
                self.info(I18N_MSGS.list_created)
                return redirect(self.get_view_name(), pk=lst.id)
            elif action == 'del':
                lst = get_object_or_404(ListModel, profile=profile, pk=pk)
                if lst.is_default:
                    self.error(I18N_MSGS.list_default_cannot_delete)
                else:
                    s = str(lst)
                    lst.delete()
                    self.info(I18N_MSGS.list_deleted % s)
                return redirect(self.get_view_name())
            elif action == 'add-task':
                task = TaskModel.objects.create(profile=profile, list_id=pk, title=I18N_MSGS.task_new_name)
                return redirect(self.get_view_name(), pk=pk)
            elif action == 'del-task':
                task_id = req.get('task_id', None)
                task = get_object_or_404(TaskModel, profile=profile, id=task_id)
                log_str = 'Task "%s" deleted by %s' % (task, profile)
                task.delete()
                log.info(log_str)
                return HttpResponse('')
            elif action == 'move-task':
                task_id = req.get('task_id', None)
                list_id = req.get('list_id', None)
                task = get_object_or_404(TaskModel, id=task_id, profile=profile)
                task.list_id = list_id
                task.save()
                log.info('Task "%s" moved to list "%s" by %s' % (task, task.list, profile))
                return HttpResponse('')
            else:
                log.warn('Invalid request. (action=%s)' % action)
                if request.is_ajax():
                    return HttpResponseBadRequest(I18N_MSGS.resp_invalid_action % action)
                else:
                    self.error(I18N_MSGS.resp_invalid_action % action)

        elif pk is not None:
            # AJAX JSON response
            pk = int(pk)
            name = req.get('name', None)
            value = req.get('value', None)
            if name in ('id', ):
                return HttpResponseBadRequest(I18N_MSGS.prop_cannot_change % name)
            if name == 'related_users':
                value = ','.join(req.getlist('value[]', []))
            if value is not None and value.strip() == '':
                value = None
            try:
                lst = ListModel.objects.get(id=pk)
                setattr(lst, name, value)
                lst.save(update_fields=[name, ])
            except Exception as err:
                log.exception(err)
                return HttpResponseBadRequest(I18N_MSGS.prop_cannot_change % (name, value))
        return HttpResponse('')
