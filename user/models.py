#!/usr/bin/env python
# coding: utf-8

from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.core.exceptions import AppRegistryNotReady

try:
    UserModel = get_user_model()
except AppRegistryNotReady:
    from django.contrib.auth.models import User as UserModel


class UserProfile(models.Model):
    """
    User profile information
    """
    id = models.BigAutoField(primary_key=True)
    # user = models.ForeignKey(to=UserModel)
    user = models.OneToOneField(UserModel)
    # email = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    timezone = models.CharField(max_length=50)
    location = models.TextField()
    lang = models.CharField(max_length=20, verbose_name='Language')
    utc_offset = models.IntegerField(verbose_name='UTC offset hours')
    img_url = models.URLField(verbose_name='Image URL')

    @property
    def email(self):
        return self.user.email

    @property
    def joined_at(self):
        return self.user.date_joined

    @property
    def screen_name(self):
        return self.user.username

