#!/usr/bin/env python
# coding: utf-8

from django.db import models
from django.core.validators import validate_comma_separated_integer_list
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import AppRegistryNotReady

try:
    UserModel = get_user_model()
except AppRegistryNotReady:
    from django.contrib.auth.models import User as UserModel


class SocialPlatform(object):
    """
    Constants and choice for social platforms.
    """
    TWITTER = 'TW'
    FACEBOOK = 'FB'
    WEIBO = 'WB'
    SocialAccountChoices = (
        (TWITTER, 'Twitter'),
        (FACEBOOK, 'Facebook'),
        (WEIBO, 'Weibo'),
    )


# ------ Common Models -----

class Config(models.Model):
    """
    Common configurations key-value list.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    timestamp = models.DateTimeField(auto_now=True)
    value = models.TextField()


class UserProfile(models.Model):
    """
    User profile information
    """
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(to=UserModel)
    # email = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    lang = models.CharField(max_length=20, default='en', verbose_name='Language')
    utc_offset = models.IntegerField(verbose_name='UTC offset hours', default=0)
    img_url = models.URLField(verbose_name='Image URL', null=True, blank=True)

    def get_email(self):
        return self.user.email

    def get_name(self):
        return self.name or self.user.username

    def get_date_joined(self):
        return self.user.date_joined


class ProfileBasedModel(models.Model):
    """
    The base model for all models which need id, profile and timestamp.
    Basically all account related models should inherit this model.
    """
    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(to=UserProfile)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SocialAccount(ProfileBasedModel):
    """
    Linked social accounts such as Twitter, Facebook and Weibo.
    """
    provider = models.CharField(max_length=2, choices=SocialPlatform.SocialAccountChoices, default=SocialPlatform.TWITTER)
    account = models.CharField(max_length=100)      # maybe screen_name, email or etc.
    followers_count = models.IntegerField()
    followings_count = models.IntegerField()
    friends_count = models.IntegerField()
    statuses_count = models.IntegerField()
    favorites_count = models.IntegerField()
    listed_count = models.IntegerField()
    profile_img_url = models.TextField()
    profile_img_url_https = models.TextField()
    created_at = models.DateTimeField()
    location = models.TextField()
    lang = models.CharField(max_length=20)
    timezone = models.CharField(max_length=50)
    utc_offset = models.IntegerField(default=0)


# ----- Spider models -----

class RawStatus(models.Model):
    """
    Base class for all raw statuses.
    """
    id = models.BigAutoField(primary_key=True)
    rawid = models.CharField(max_length=50, db_index=True, unique=True, verbose_name='Raw ID')
    created_at = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now=True)
    username = models.CharField(max_length=100, db_index=True, verbose_name='Social Screen Name')
    text = models.TextField(verbose_name='Status Text')
    source = models.CharField(max_length=2, choices=SocialPlatform.SocialAccountChoices)
    parsed = models.BooleanField(default=False)
    raw = models.TextField(verbose_name='Raw Data')

#     class Meta:
#         abstract = True
#
#
# class RawTweet(RawStatus):
#     """
#     Raw status of twitter (tweets) from spider.
#     """
#     def formatted_raw_json(self):
#         return self.raw
#
#
# class RawFacebookStatus(RawStatus):
#     """
#     Raw status of Facebook from spider.
#     """
#     pass
#
#
# class RawWeiboStatus(RawStatus):
#     """
#     Raw status of Weibo from spider.
#     """
#     pass


# ----- Task models -----

# class TaskType(object):
#     TODO = 'T'
#     WISH = 'W'
#     APPOINTMENT = 'A'
#     TaskTypeChoice = (
#         (TODO, 'Todo'),
#         (WISH, 'Wish'),
#         (APPOINTMENT, 'Appointment')
#     )


class Task(ProfileBasedModel):
    """
    Base task model for todo, wish and schedule appointment
    """
    status = models.OneToOneField(to=RawStatus)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=200)
    text = models.TextField(verbose_name='Origin Text', null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    labels = models.TextField(db_index=True, null=True, blank=True)
    # type = models.CharField(max_length=1, choices=TaskType)

    class Meta:
        abstract = True


class Todo(Task):
    """
    Todo entity
    """
    deadline = models.DateTimeField(null=True, blank=True)


class Appointment(Task):
    """
    Schedule appointment
    """
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    location = models.TextField()


class Wish(Task):
    """
    A wish means a thing you want (maybe a travel, a bag or even a lover.)
    """
    img = models.BinaryField()


class WishList(ProfileBasedModel):
    """
    A wish list contains one or more things you want.
    """
    reminder = models.DateTimeField()
    wishers = models.TextField(validators=[validate_comma_separated_integer_list])


class TodoList(ProfileBasedModel):
    """
    """
    reminder = models.DateTimeField()
    coworkers = models.TextField(validators=[validate_comma_separated_integer_list])


class WishListRel(models.Model):
    """
    Wish-list and wish relationship. Wishes on a wish-list of a user.
    """
    list = models.ForeignKey(to=WishList)
    task = models.ForeignKey(to=Wish)

    class Meta:
        unique_together = ('list', 'task')


class TodoListRel(models.Model):
    """
    Wish-list and wish relationship. Wishes on a wish-list of a user.
    """
    list = models.ForeignKey(to=TodoList)
    task = models.ForeignKey(to=Wish)

    class Meta:
        unique_together = ('list', 'task')


# ========== Admin Pages ==========

class RawStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'rawid', 'source', 'created_at', 'username', 'text', 'timestamp')
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


# @admin.register(RawTweet)
# class RawTweetAdmin(RawStatusAdmin):
#     """
#     Admin page for RawTweet
#     """
#     pass


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    """
    Admin page for configurations.
    """
    list_display = ('id', 'name', 'value')
    list_display_links = ('id', 'name')


# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     """
#     User profile admin page
#     """
#     pass