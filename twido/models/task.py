#!/usr/bin/env python
# coding: utf-8

"""
Task and list related models
"""
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import validate_comma_separated_integer_list
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from .common import ProfileBasedModel, UserProfile
from .consts import TaskStatus
from .social import SocialAccount
from .spider import RawStatus

import logging
log = logging.getLogger(__name__)


class List(ProfileBasedModel):
    """
     A list contains one or more things you want or want to do. (todolist, wishlist, ...)
    """
    name = models.CharField(max_length=100)
    reminder = models.DateTimeField(null=True, blank=True)
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

        default_list.text = _('The default list. It will be created automatically (even if you delete it).')
        default_list.save(is_default=True)

        return default_list

    @property
    def is_default(self):
        return self.name == self.__default_name

    @property
    def default(self):
        return self.get_default(self.profile)

    def get_related_profiles(self):
        return UserProfile.objects.filter(username__in=(self.related_users.split(',') or ''))

    def get_related_usernames(self):
        return self.related_users.split(',')

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
    status = models.SmallIntegerField(choices=TaskStatus.Choices, default=TaskStatus.NEW, db_index=True)
    text = models.TextField(null=True, blank=True)
    labels = models.TextField(null=True, blank=True)
    reminder = models.DateTimeField(null=True, blank=True)
    list = models.ForeignKey(to=List)

    content = models.TextField(null=True, blank=True)
    social_account = models.ForeignKey(to=SocialAccount, db_index=True, null=True, blank=True)
    raw = models.OneToOneField(to=RawStatus, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super(Task, self).save(*args, **kwargs)

    def get_owner_name(self):
        if self.profile and self.profile != UserProfile.get_sys_profile():
            return self.profile.get_name()
        elif self.social_account:
            return self.social_account.name or self.social_account.account

    def get_status_text(self):
        return TaskStatus.get_text(self.status)

    def get_status_glyphicon(self):
        return TaskStatus.get_glyphicon(self.status)

    def get_view_path(self):
        return reverse('task', args=(self.id, ))

    def __str__(self):
        return '%s (id=%d)' % (self.title, self.id)


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
