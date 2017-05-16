#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.core.exceptions import AppRegistryNotReady
from django.utils.translation import ugettext_lazy as _

try:
    UserModel = get_user_model()
except AppRegistryNotReady:
    from django.contrib.auth.models import User as UserModel

from twido.models import UserProfile

# class User(AbstractUser):
#     """
#     Users within the Django authentication system are represented by this
#     model.
#
#     Username, password and email are required. Other fields are optional.
#     """
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['email']
#
#     class Meta(AbstractUser.Meta):
#         swappable = 'AUTH_USER_MODEL'
#
#     email = models.EmailField(
#         _('email address'),
#         unique=True,
#         db_index=True,
#         error_messages={
#             'unique': _("A user with that email already exists."),
#         },
#     )
#
#     username = models.CharField(_('account name'), max_length=50, null=True, blank=True)
#
