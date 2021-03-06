#!/usr/bin/env python
# coding: utf-8

"""
Task and list related models
"""
from datetime import timedelta
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.core.validators import validate_comma_separated_integer_list
from django.utils.functional import SimpleLazyObject
from django.utils.translation import ugettext_lazy as _, pgettext_lazy, ugettext_noop
from django.db import transaction
from .common import ProfileBasedModel, UserProfile
from .consts import TaskStatus, Visibility
from pyutils.langutil import PropertyDict
from .social import SocialAccount
from .spider import RawStatus

import simplejson as json
import logging
from twido.parser import Timex3Parser

log = logging.getLogger(__name__)


class List(ProfileBasedModel):
    """
     A list contains one or more things you want or want to do. (todolist, wishlist, ...)
    """
    name = models.CharField(max_length=100)
    reminder = models.DateTimeField(null=True, blank=True)
    visibility = models.IntegerField(choices=Visibility.Choices, default=Visibility.PUBLIC, db_index=True)
    related_users = models.TextField(validators=[validate_comma_separated_integer_list], null=True, blank=True,
                                     db_index=True, verbose_name='Related Persons (comma separated)')
    text = models.TextField(null=True, blank=True)

    # class Meta:
    #     unique_together = ('profile', 'name')

    __default_name = '__default__'

    def __str__(self):
        return "%s (id=%d)" % (self.name, self.id)

    @classmethod
    def get_default(cls, profile):
        try:
            default_list = cls.objects.get(name=cls.__default_name, profile=profile)
        except cls.DoesNotExist:
            default_list = cls(name=cls.__default_name, profile=profile)
            default_list.text = ugettext_noop('The default list contains unlisted tasks.')
            default_list.save(is_default=True)
        return default_list

    @property
    def is_default(self):
        return self.name == self.__default_name

    @property
    def is_sys(self):
        return self.name.startswith('__')

    @property
    def default(self):
        return self.get_default(self.profile)

    def get_name(self):

        if self.is_default:
            return pgettext_lazy('sys list', 'default')
        elif self.is_sys:
            return pgettext_lazy('sys list', self.name.lstrip('_'))
        else:
            return self.name

    def get_related_profiles(self):
        return UserProfile.objects.filter(username__in=(self.related_users.split(',') or ''))

    def get_related_usernames(self):
        return self.related_users.split(',')

    def get_visibility_text(self):
        return Visibility.get_text(self.visibility)

    def get_visibility_icon(self):
        return Visibility.get_icon(self.visibility)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, is_default=False):
        if not is_default and self.name.lower() == self.__default_name:
            raise AttributeError('List name can not be "%s" (reversed default name). ' % self.name)
        return super(List, self).save(force_insert=force_insert, force_update=force_update,
                                      using=using, update_fields=update_fields)

    def delete(self, using=None, keep_parents=False):
        s = str(self)
        log.debug('deleting list %s' % s)
        with transaction.atomic():
            # This query ref to Task. So to avoid recursive reference, need to put List in same file with Task
            Task.objects.filter(list=self, profile=self.profile).update(list=self.get_default(self.profile))
            log.debug('all tasks in todo list %s are moved to default list.' % s)
            super(List, self).delete(using=using, keep_parents=keep_parents)
            log.info('todo list %s is deleted.' % s)


class Task(ProfileBasedModel):
    """
    Base task model for todo, wish and schedule appointment
    """
    created_at = models.DateTimeField(editable=False)
    title = models.CharField(max_length=100)
    status = models.IntegerField(choices=TaskStatus.Choices, default=TaskStatus.NEW, db_index=True)
    visibility = models.IntegerField(choices=Visibility.Choices, default=Visibility.PUBLIC, db_index=True)
    text = models.TextField(null=True, blank=True)
    labels = models.TextField(null=True, blank=True)
    due = models.DateTimeField(null=True, blank=True, db_index=True)
    list = models.ForeignKey(to=List)
    social_account = models.ForeignKey(to=SocialAccount, db_index=True, null=True, blank=True)

    content = models.TextField(null=True, blank=True)
    raw = models.OneToOneField(to=RawStatus, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super(Task, self).save(*args, **kwargs)

    def get_owner_name(self):
        if self.profile and not self.profile.is_sys:
            return self.profile.get_name()
        elif self.social_account:
            return self.social_account.name or self.social_account.account

    def get_at_name(self):

        if self.profile.is_faked:
            uname = self.social_account.account
        else:
            uname = self.profile.username
        return '@' + uname

    def get_status_text(self):
        return TaskStatus.get_text(self.status)

    def get_status_icon(self):
        return TaskStatus.get_icon(self.status)

    def get_visibility_text(self):
        return Visibility.get_text(self.visibility)

    def get_visibility_icon(self):
        return Visibility.get_icon(self.visibility)

    def get_view_path(self):
        return reverse('task', args=(self.id, ))

    def __str__(self):
        return '%s (id=%d)' % (self.title, self.id)


class TaskMeta(models.Model):
    task = models.OneToOneField(to=Task, related_name='meta')
    timex = models.TextField(null=True, blank=True)
    dates = models.TextField(null=True, blank=True)
    tags = models.TextField(null=True, blank=True)
    persons = models.TextField(null=True, blank=True)
    simple_text = models.TextField(null=True, blank=True)

    _tags = []
    _dates = []

    def highlight_timex(self):
        return Timex3Parser.highlight(self.timex)

    def get_dates(self):
        if not self._dates:
            self._dates = json.loads(self.dates)
        return self._dates

    def get_tags(self):
        if not self._tags:
            self._tags = json.loads(self.tags)
        return self._tags

    def save(self, *args, **kwargs):
        super(TaskMeta, self).save(*args, **kwargs)
        self._tags = []
        self._dates = []


class SysList(object):
    """
    System pre-defined query list
    """

    soon_days = 3

    def __init__(self, profile, list_model=List, task_model=Task, entries_per_page=10):
        self.ListModel = list_model
        self.TaskModel = task_model
        self.profile = profile
        self.entries = entries_per_page
        self._meta = PropertyDict((
            ('__today', PropertyDict(
                name='__today',
                title=pgettext_lazy('sys list', 'today'),   # for i18n text generation usage
                text=ugettext_noop('Tasks need to be done by today. (including expired)'),
                tasks=SimpleLazyObject(self.__get_today_tasks)
            )),
            ('__coming', PropertyDict(
                name='__coming',
                title=pgettext_lazy('sys list', 'coming'),    # for i18n text generation usage
                text=ugettext_noop('Tasks in near future'),
                tasks=SimpleLazyObject(self.__get_coming_tasks)
            )),
            ('__expired', PropertyDict(
                name='__expired',
                title=pgettext_lazy('sys list', 'expired'),   # for i18n text generation usage
                text=ugettext_noop('Tasks passed the deadline.'),
                tasks=SimpleLazyObject(self.__get_expired_tasks)
            )),
            ('__all', PropertyDict(
                name='__all',
                title=pgettext_lazy('sys list', 'all'),   # for i18n text generation usage
                text=ugettext_noop('All my tasks.'),
                tasks=SimpleLazyObject(self.__get_all_tasks)
            )),
        ))

        # for translation usage (not working)
        # for meta in self._meta.values():
        #     meta.title = pgettext_lazy('sys list', meta.name.lstrip('_'))

        self._lists = PropertyDict()

    @property
    def all(self):
        if not self._lists:
            for name in self._meta.keys():
                self.get(name)
        return self._lists

    def __getitem__(self, item):
        return self.get(item)

    def get(self, name):
        if name not in self._lists:
            meta = self._meta[name]
            lst, created = self.ListModel.objects.get_or_create(profile=self.profile, name=name)
            if created:
                lst.text = meta.text
                lst.visibility = False
                lst.save()
                log.debug('list "%s" created.' % lst)
            lst.tasks = meta.tasks
            self._lists[name] = lst
        return self._lists[name]

    def __get_today_tasks(self):
        now = timezone.now()
        today = timezone.datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        tomorrow = today + timedelta(days=1)
        return self.TaskModel.objects.filter(profile=self.profile, due__range=(today, tomorrow))

    def __get_coming_tasks(self):
        now = timezone.now()
        soon = now + timedelta(days=self.soon_days)
        return self.TaskModel.objects.filter(profile=self.profile).filter(
            Q(due__gt=now) & Q(due__lt=soon) | Q(due=None))

    def __get_expired_tasks(self):
        return self.TaskModel.objects.filter(profile=self.profile, due__lt=timezone.now()).exclude(
            status__in=(TaskStatus.DONE, TaskStatus.CANCEL))

    def __get_all_tasks(self):
        return self.TaskModel.objects.filter(profile=self.profile)


class SmartList(object):
    """
    User defined search list
    """
    pass


# class Todo(Task):
#     """
#     Todo entity
#     """
#     # list = models.ForeignKey(to=TodoList)
#     deadline = models.DateTimeField(null=True, blank=True)
#
#     def get_view_path(self):
#         return reverse('todo', args=(self.id,))
#
#
# class Appointment(Task):
#     """
#     Schedule appointment
#     """
#     start_at = models.DateTimeField()
#     end_at = models.DateTimeField()
#     location = models.TextField()
#
#
# class Wish(Task):
#     """
#     A wish means a thing you want (maybe a travel, a bag or even a lover.)
#     """
#     # list = models.ForeignKey(to=WishList)
#     img = models.BinaryField()
