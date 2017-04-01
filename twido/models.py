#!/usr/bin/env python
# coding: utf-8

from django.db import models
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import AppRegistryNotReady

try:
    UserModel = get_user_model()
except AppRegistryNotReady:
    from django.contrib.auth.models import User as UserModel


# ------ Common Models -----

class UserProfile(models.Model):
    """
    User profile information
    """
    user = models.ForeignKey(to=UserModel)


class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(to=UserProfile)
    timestamp = models.DateTimeField(auto_now=True)


class Config(models.Model):
    """
    Common configurations key-value list.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    timestamp = models.DateTimeField(auto_now=True)
    value = models.TextField()


class SocialAccount(BaseModel):
    """
    Linked social accounts such as Twitter, Facebook and Weibo.
    """
    pass


class Task(BaseModel):
    """
    User tasks including todo and schedule.
    """
    pass


# ----- Spider models -----

class RawEntry(models.Model):
    """
    Base class for all raw entries.
    """
    id = models.BigAutoField(primary_key=True)
    rawid = models.CharField(max_length=50, db_index=True, unique=True, verbose_name='Raw ID')
    created_at = models.DateTimeField()
    timestamp = models.DateTimeField(auto_now=True)
    username = models.CharField(max_length=100, db_index=True, verbose_name='Social Screen Name')
    text = models.TextField(verbose_name='Entry Text')
    raw = models.TextField(verbose_name='Raw Data')

    class Meta:
        abstract = True


class RawTweet(RawEntry):
    """
    Raw tweets of twitter from spider.
    """
    def formatted_raw_json(self):
        return self.raw


class RawFacebook(RawEntry):
    """
    Raw entry of Facebook from spider.
    """
    pass


class RawWeibo(RawEntry):
    """
    Raw entry of Weibo from spider.
    """
    pass


# ========== Admin Pages ==========

class RawEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'rawid', 'created_at', 'username', 'text', 'timestamp')
    # exclude = ['raw']
    # fieldsets = (
    #     (None, {
    #         'fields': ('id', 'created_at', 'user', 'text',)
    #     }),
    #     ('Advanced options', {
    #         'classes': ('collapse',),
    #         'fields': ('raw', ),
    #     }),
    # )


@admin.register(RawTweet)
class RawTweetAdmin(RawEntryAdmin):
    """
    Admin page for RawTweet
    """
    pass


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    """
    Admin page for configurations.
    """
    list_display = ('id', 'name', 'value')
    list_display_links = ('id', 'name')