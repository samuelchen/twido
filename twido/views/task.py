#!/usr/bin/env python
# coding: utf-8

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView, DetailView, CreateView, DeleteView
from django.utils.translation import ugettext_lazy as _
from ..models import Todo,  TodoList, TaskStatus
from .base import BaseViewMixin
from .common import paginate
# from .common import I18N_MSGS

import logging
log = logging.getLogger(__name__)


class I18N_MSGS(object):
    # HTTP Bad Responses
    resp_invalid_action = _('Invalid request. (action=%s)')

    # UI List messages
    list_new_name = _('New List')
    list_default_cannot_delete = _('Default list can not be deleted.')
    list_created = _('New list is created.')
    list_deleted = _('Todo list "%s" was deleted.')

    # UI task messages
    # task_deleted_by = _('Todo task "%(task)s" deleted by %(profile)s')
    task_new_name = _('New Task')

    # model
    primary_key_is_none = _('Primary key is None')
    prop_cannot_be = _('"%(prop)s" can not be "%(value)s"')
    prop_cannot_change = _('"%s" can not be changed.')


class TaskView(TemplateView, BaseViewMixin):

    def get_task_model(self):
        raise NotImplementedError

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


class TaskListView(TemplateView, BaseViewMixin):

    def get_list_model(self):
        raise NotImplementedError

    def get_task_model(self):
        raise NotImplementedError

    def get_view_name(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):

        context = super(TaskListView, self).get_context_data(**kwargs)
        ListModel = self.get_list_model()
        TaskModel = self.get_task_model()

        profile = self.request.user.profile
        p = self.request.GET.get('p')   # current page

        if 'pk' in context:
            pk = context['pk']
            thelist = get_object_or_404(ListModel, profile=profile, id=pk)
        else:
            thelist = ListModel.get_default(profile)

        context['thelist'] = thelist

        if 'page' not in context:
            context['page'] = paginate(TaskModel.objects.filter(profile=profile, list=thelist).select_related('list'), cur_page=p, entries_per_page=10)
        if 'list' not in context:
            context['lists'] = ListModel.objects.filter(profile=profile).all()
        if 'taskstatus' not in context:
            context['taskstatus'] = TaskStatus

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
                                              name=(I18N_MSGS.list_new_name + ' ' + str(TodoList.objects.last().id)))
                self.info(I18N_MSGS.list_created)
                return redirect(self.get_view_name(), pk=lst.id)
            elif action == 'del':
                lst = get_object_or_404(ListModel, profile=profile, pk=pk)
                if lst.is_default:
                    self.error(I18N_MSGS.list_default_cannot_delete)
                else:
                    lst.delete()
                    self.info(I18N_MSGS.list_deleted % lst.name)
                return redirect(self.get_view_name())
            elif action == 'add-task':
                TaskModel.objects.create(profile=profile, list_id=pk, title=I18N_MSGS.task_new_name)
                return redirect(self.get_view_name(), pk=pk)
            elif action == 'del-task':
                task_id = req.get('task_id', None)
                task = get_object_or_404(TaskModel, profile=profile, id=task_id)
                log_str = 'Task "%s" deleted by %s' % (task, profile)
                task.delete()
                log.info(log_str)
                return HttpResponse('')
                # return redirect('todolist')
            elif action == 'move-task':
                task_id = req.get('task_id', None)
                list_id = req.get('list_id', None)
                task = get_object_or_404(TaskModel, id=task_id, profile=profile)
                # lst = get_object_or_404(TodoList, profile=profile, id=list_id)
                task.list_id = list_id
                task.save()
                log.info('Todo task "%s" moved to list "%s" by %s' % (task, task.list, profile))
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
            # print(name, '-', value)
            try:
                lst = TodoList.objects.get(id=pk)
                setattr(lst, name, value)
                lst.save(update_fields=[name, ])
            except Exception as err:
                log.exception(err)
                return HttpResponseBadRequest(I18N_MSGS.prop_cannot_change % (name, value))
        return HttpResponse('')


class TodoListView(TaskListView):

    def get_list_model(self):
        return TodoList

    def get_task_model(self):
        return Todo

    def get_view_name(self):
        return 'todolist'

    def get_context_data(self, **kwargs):
        context = super(TodoListView, self).get_context_data(**kwargs)
        context['todolists'] = context['lists']
        context['fields'] = ('status', 'title', 'text', 'labels', 'deadline')
        context['editables'] = ('status', 'title', 'text', 'labels', 'deadline')
        context['actions'] = ('detail', 'del')
        return context


class TodoView(TaskView):

    def get_task_model(self):
        return Todo


    # def get_context_data(self, **kwargs):
    #     context = super(TodoView, self).get_context_data(**kwargs)
    #     context['fields'] = ('status', 'title', 'deadline')
    #     return context