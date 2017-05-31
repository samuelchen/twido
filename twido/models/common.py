#!/usr/bin/env python
# coding: utf-8

"""
Common models
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import AppRegistryNotReady
from django.db import models
from django.utils import timezone
from django.utils.translation import pgettext_lazy
from .consts import Gender

try:
    UserModel = get_user_model()
except AppRegistryNotReady:
    from django.contrib.auth.models import User as UserModel

import logging
log = logging.getLogger(__name__)


class UserProfile(models.Model):
    """
    User Profile.

    Django User is used for authorization (login/logout/register).
    User.username will always be set to User.email.
    The Django User.email field is useless.

    email -> login account.
    username -> user.username. Account ID.
    name -> display/nick name. user.first_name/last_name will be ignore
    """
    id = models.BigAutoField(primary_key=True)

    # TODO: null or not ? make __sys__ user locked ?
    # null means faked profile
    user = models.OneToOneField(to=UserModel, related_name='profile', db_index=True, null=True, blank=True)
    email = models.CharField(max_length=100, unique=True, db_index=True, editable=False)    # user.email
    username = models.CharField(max_length=100, unique=True, db_index=True, null=True)
    created_at = models.DateTimeField(editable=False)

    name = models.CharField(max_length=100, null=True, blank=True)  # real/nick/display name
    gender = models.CharField(max_length=1, default=Gender.PRIVATE, choices=Gender.Choices)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    lang = models.CharField(max_length=20, default='en', verbose_name='Language')
    utc_offset = models.IntegerField(verbose_name='UTC offset hours', default=0)
    img_url = models.URLField(verbose_name='Image URL', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    __sys_profile = None
    __sys_profile_uname = '__sys__'

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super(UserProfile, self).save(*args, **kwargs)

    @classmethod
    def init_data(cls):
        p, created = cls.objects.get_or_create(username=cls.__sys_profile_uname)
        if created:
            p.email = cls.__sys_profile_uname + '@localhost'
            p.name = pgettext_lazy('system account name', 'SYS')
            p.save()
            log.info('System profile (%s) is created.' % cls.__sys_profile_uname)
        cls.__sys_profile = p

    @classmethod
    def get_sys_profile(cls):
        if cls.__sys_profile is None:
            cls.init_data()
        return cls.__sys_profile

    @classmethod
    def get_sys_profile_username(cls):
        return cls.__sys_profile_uname

    def get_email(self):
        return self.email

    def get_name(self):
        """
        Return a display name. (never return email or user.username)
        :return a display name
        """
        if self.name:
            return self.name
        elif self.username:
            return self.username
        elif self.is_faked:
            return self.id
        return self.user.id

    def get_date_joined(self):
        return self.created_at

    def get_img_url(self):
        if self.img_url:
            return self.img_url
        else:
            return Gender.get_img(self.gender)

    def get_gender_icon(self):
        return Gender.get_icon(self.gender)

    def get_gender_text(self):
        return Gender.get_text(self.gender)

    @property
    def is_faked(self):
        return self.user is None

    def __str__(self):
        return '%s (id=%d)' % (self.email, self.id)


class ProfileBasedModel(models.Model):
    """
    The base model for all models which need id, profile and timestamp.
    Basically all account related models should inherit this model.
    """
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(to=UserProfile, db_index=True)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Config(ProfileBasedModel):
    """
    Common configurations name-value list.
    Represents system configurations if self.profile is None
    """
    name = models.CharField(max_length=100, db_index=True)
    value = models.TextField()

    class Meta:
        unique_together = ('profile', 'name')

    def __str__(self):
        return '%s=%s' % (self.name, self.value)

    @classmethod
    def get_user_conf(cls, profile, name):
        try:
            return cls.objects.get(profile=profile, name=name)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_or_create_user_conf(cls, profile, name):
        return cls.objects.get_or_create(profile=profile, name=name)

    @classmethod
    def set_user_conf(cls, profile, name, value):
        opt, created = cls.objects.get_or_create(profile=profile, name=name)
        opt.value = value
        opt.save()

    @classmethod
    def get_sys_conf(cls, name):
        try:
            return cls.objects.get(profile=UserProfile.get_sys_profile(), name=name)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_or_create_sys_conf(cls, name):
        return cls.objects.get_or_create(profile=UserProfile.get_sys_profile(), name=name)

    @classmethod
    def set_sys_conf(cls, name, value):
        opt, created = cls.objects.get_or_create(profile=UserProfile.get_sys_profile(), name=name)
        opt.value = value
        opt.save()
