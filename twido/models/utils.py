#!/usr/bin/env python
# coding: utf-8

"""
Model utilities
"""
from django.db import transaction
from . import List, Task, SocialAccount, UserProfile, Config


@transaction.atomic
def replace_profile(origin_profile, new_profile, social_platform='', del_origin=True):
    """
    Replace resources of current profile to anther profile
    NOTICE: Need to update all ProfileBasedModel
    TODO: performance
    :param origin_profile:
    :param new_profile:
    :return:
    """
    origin_default_list = List.get_default(origin_profile)
    new_default_list = List.get_default(new_profile)
    List.objects.filter(profile=origin_profile).exclude(name__istartswith='__').update(profile=new_profile)
    Task.objects.filter(profile=origin_profile, list=origin_default_list).update(
        profile=new_profile, list=new_default_list)
    Task.objects.filter(profile=origin_profile).update(profile=new_profile)
    if social_platform:
        SocialAccount.objects.filter(platform=social_platform).update(profile=new_profile)
    else:
        SocialAccount.objects.update(profile=new_profile)

    if del_origin:
        # Config.objects.filter(profile=origin_profile).delete()
        # Config and others should be deleted when ForeignKey profile deleted (ON DELETE CASCADE).
        # https://docs.djangoproject.com/en/1.11/topics/db/queries/#deleting-objects
        origin_profile.user.delete()
        # origin_profile.delete()
