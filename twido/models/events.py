#!/usr/bin/env python
# coding: utf-8

"""
To process model signals
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import AppRegistryNotReady
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.utils import timezone
from ..apps import TwidoAppConfig
from .common import UserProfile
from .list import List

try:
    UserModel = get_user_model()
except AppRegistryNotReady:
    from django.contrib.auth.models import User as UserModel

import logging
log = logging.getLogger(__name__)

#
# @receiver(post_save, sender=UserModel)
# def post_save_user(sender, **kwargs):
#     user = kwargs['instance']
#     created = kwargs['created']
#
#     # ensure user.username is user.email.
#     if user.email and user.username != user.email:
#         user.username = user.email
#         user.save()
#
#     if created and user is not None:
#         profile = UserProfile(user=user)
#         profile.email = user.email
#         profile.name = user.email[:user.email.find('@')]
#         profile.username = profile.name + str(int(timezone.now().timestamp()))
#         profile.save()
#
#
# @receiver(post_save, sender=UserProfile)
# def post_save_profile(sender, **kwargs):
#     created = kwargs['created']
#
#     if created:
#         profile = kwargs['instance']
#         if profile.user is None:
#             profile.user = UserModel(email=profile.email, username=profile.email)
#             profile.user.save()
#             List.init_data(profile)
#
#
# @receiver(post_migrate)
# def post_migrate(sender, **kwargs):
#     if sender.name == TwidoAppConfig.name:
#         UserProfile.init_data()
#
