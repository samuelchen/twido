#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _, pgettext_lazy, pgettext
from django.core import serializers
from wsgiref.util import FileWrapper
from io import StringIO
from pyutils.django.response import download_file_response
import simplejson as json
from pyutils.json import to_serializable

from ..models import Task,  List, TaskStatus, SysList
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
    list_cannot_change_sys = _('System list is not able to be changed.')
    list_name_cannot_start_with_dbl_underscore = _('List name can not start with double underscores "__" .')

    # UI task messages
    task_new_name = _('New Task')

    # model
    prop_cannot_change = _('"%s" can not be changed.')

    file_incorrect_format = _('File is broken or incorrect content.')
    list_imported = _('List with tasks is imported successfully.')

    imported = pgettext_lazy('list prefix', 'imported')


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
        log.debug('ListModel is %s' % ListModel)
        log.debug('TaskModel is %s' % TaskModel)

        profile = self.request.user.profile
        p = self.request.GET.get('p', 1)   # current page of tasks
        context['p'] = p
        log.debug('current page of tasks: %s (%s) ' % (p, type(p)))

        if 'pk' in context:
            pk = context['pk']
            thelist = get_object_or_404(ListModel, profile=profile, id=pk)
            log.debug('list view pk: %s' % pk)
        else:
            thelist = ListModel.get_default(profile)

        log.debug('thelist: %s' % thelist)

        context['thelist'] = thelist
        context['lists'] = ListModel.objects.filter(profile=profile).all()
        sys_list = SysList(profile=profile, list_model=ListModel, task_model=TaskModel)
        context['sys_lists'] = sys_list.all

        # tasks in current page
        if thelist.is_sys and not thelist.is_default:
            context['page'] = paginate(sys_list[thelist.name].tasks,
                                       cur_page=p, entries_per_page=10)
        else:
            context['page'] = paginate(TaskModel.objects.filter(profile=profile, list=thelist).select_related('list'),
                                       cur_page=p, entries_per_page=10)

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
        profile = request.user.profile
        action = req.get('action', None)
        log.debug('list view action: %s' % action)

        if 'pk' in kwargs:
            pk = kwargs['pk']
        else:
            pk = ListModel.get_default(profile).id

        log.debug('list view pk: %s' % pk)

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
            elif action == 'export':
                lst = get_object_or_404(ListModel, profile=profile, pk=pk)
                list_dict = lst.to_dict()
                del list_dict['id']
                if lst.is_sys:
                    list_dict['name'] = pgettext('sys_list', lst.get_name())
                    sys_list = SysList(profile=profile)
                    task_set = sys_list[lst.name].tasks
                else:
                    task_set = lst.task_set.all()
                tasks = []
                for task in task_set:
                    task_dict = task.to_dict()
                    del task_dict['id']
                    del task_dict['list_id']
                    tasks.append(task_dict)
                list_dict['tasks'] = tasks

                data = json.dumps(list_dict, ensure_ascii=False, indent=2, default=to_serializable)
                # l = len(data)

                # gen file download
                stream_buf = StringIO(data)
                stream_buf.seek(0)
                f = FileWrapper(stream_buf)
                response = HttpResponse(f, content_type='application/json')
                response['Content-Disposition'] = 'attachment; filename=lists.json'
                # response = download_file_response(stream_buf, filename='lists.json', content_type='application/json')
                # response['Content-Length'] = l
                return response
            elif action == 'import':
                # TODO: handle big file and stream.
                file = request.FILES.get('choose_file')
                list_dict = None
                if file:
                    log.debug('importing file: name="%s" size=%s' % (file.name, file.size))
                    s = file.read()
                    file.close()
                    try:
                        list_dict = json.loads(s)
                        print(list_dict)
                    except json.JSONDecodeError as err:
                        log.debug('import list error: ' + str(err))
                        self.error(I18N_MSGS.file_incorrect_format)
                if list_dict:
                    try:
                        lst = ListModel()
                        lst.from_dict(list_dict)
                        lst.name = '%s (%s)' % (lst.name, I18N_MSGS.imported)
                        lst.profile = profile
                        lst.save()

                        if 'tasks' in list_dict:
                            tasklist = list_dict['tasks']
                            tasks = []
                            for task in tasklist:
                                t = TaskModel()
                                t.from_dict(task)
                                t.profile = profile
                                t.list = lst
                                t.social_account = None
                                t.raw = None
                                tasks.append(t)
                            TaskModel.objects.bulk_create(tasks)
                            self.success(I18N_MSGS.list_imported)
                            return redirect(self.get_view_name(), pk=lst.id)
                    except Exception as err:
                        log.exception(err)
                        self.error(I18N_MSGS.file_incorrect_format)

                return self.get(request, *args, **kwargs)

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
            if name == 'name' and value.startswith('__'):
                return HttpResponseBadRequest(I18N_MSGS.list_name_cannot_start_with_dbl_underscore)
            # TODO: datetime timezone convert
            # if name == 'reminder':
            #     value = parse_datetime(value).replace(tzinfo=config.timezone) #timezone.utc)
            if value is not None and value.strip() == '':
                value = None
            try:
                lst = ListModel.objects.get(id=pk)
                if lst.is_sys:
                    return HttpResponseBadRequest(I18N_MSGS.list_cannot_change_sys)
                setattr(lst, name, value)
                lst.save(update_fields=[name, ])
            except Exception as err:
                log.exception(err)
                return HttpResponseBadRequest(I18N_MSGS.prop_cannot_change % (name, value))

        return HttpResponse('')
