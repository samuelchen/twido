#!/usr/bin/env python
# coding: utf-8

from django.db import models
from django.core.validators import validate_comma_separated_integer_list
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import AppRegistryNotReady
from django.db.models.signals import post_save
from django.dispatch import receiver
# from simple_email_confirmation.models import SimpleEmailConfirmationUserMixin
from django.templatetags.static import static

try:
    UserModel = get_user_model()
except AppRegistryNotReady:
    from django.contrib.auth.models import User as UserModel

import logging
log = logging.getLogger(__name__)


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
    User Profile.

    The Django User model's "email" field is useless.

    email -> login account.
    username -> user.username. Account ID.
    name -> display/nick name. user.first_name/last_name will be ignore
    """
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(to=UserModel, related_name='profile', db_index=True, null=True, blank=True)    # null means faked profile
    email = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)    # user.email
    username = models.CharField(max_length=100, unique=True, db_index=True)        # user.username

    name = models.CharField(max_length=100, null=True, blank=True)  # nick name, user.first_name/user.last_name
    gender = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    lang = models.CharField(max_length=20, default='en', verbose_name='Language')
    utc_offset = models.IntegerField(verbose_name='UTC offset hours', default=0)
    img_url = models.URLField(verbose_name='Image URL', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    def get_email(self):
        return self.email

    def get_name(self):
        """
        :return a display name
        """
        if self.name:
            return self.name
        elif self.username:
            return self.username
        elif self.is_faked:
            return self.get_email() or self.id
        return self.user.username

    def get_date_joined(self):
        if self.is_faked:
            return self.timestamp
        return self.user.date_joined

    def get_img_url(self):
        return self.img_url or (static('twido/img/avatar-man.png') if self.gender else static('twido/img/avatar-woman.png'))

    @property
    def is_faked(self):
        return self.user is None


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
    Social accounts such as Twitter, Facebook and Weibo.
    """
    provider = models.CharField(max_length=2, choices=SocialPlatform.SocialAccountChoices, default=SocialPlatform.TWITTER)
    account = models.CharField(max_length=100)      # maybe screen_name, email or etc.
    name = models.CharField(max_length=100, null=True, blank=True)  # nick name, user.first_name/user.last_name

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

    def __str__(self):
        return 'status(%s, id=%s, rawid=%s, user=%s, text="%s")' % (
            self.source, self.id, self.rawid, self.username,
            self.text if len(self.text) <= 20 else self.text[0:20] + '...')


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


class List(ProfileBasedModel):
    """
     A list contains one or more things you want. (todolist, wishlist, ...)
    """
    name = models.CharField(max_length=50)
    reminder = models.DateTimeField(null=True, blank=True)
    related_users = models.TextField(validators=[validate_comma_separated_integer_list], null=True, blank=True,
                                     db_index=True, verbose_name='Related usernames (comma separated)')
    text = models.TextField(null=True, blank=True)

    __default_name = 'default'
    __default = None

    @classmethod
    def init_data(cls, profile):
        l, created = cls.objects.get_or_create(name=cls.__default_name, profile=profile)
        if created:
            l.save()

    @classmethod
    def get_default(cls, profile):
        if cls.__default is None:
            # cls.__default = cls.objects.get(name=cls.__default_name, property=profile)
            cls.__default, created = cls.objects.get_or_create(name=cls.__default_name, profile=profile)
            if created:
                # TODO: update some default values and save
                cls.__default.text = 'The default list. It will be created automatically.'
                cls.__default.save()

        return cls.__default

    def get_related_profiles(self):
        return UserProfile.objects.filter(username__in=self.related_users or '')

    def get_related_usernames(self):
        return self.related_users.split(',')

    class Meta:
        abstract = True


class WishList(List):
    """
    A wish list contains one or more things you want.
    """
    pass


class TodoList(List):
    """
    A wish list contains one or more things you want to do or buy.
    """
    pass


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
    list = models.ForeignKey(to=TodoList)
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
    list = models.ForeignKey(to=WishList)
    img = models.BinaryField()



# class WishListRel(models.Model):
#     """
#     Wish-list and wish relationship. Wishes on a wish-list of a user.
#     """
#     list = models.ForeignKey(to=WishList)
#     task = models.ForeignKey(to=Wish)
#
#     class Meta:
#         unique_together = ('list', 'task')


# class TodoListRel(models.Model):
#     """
#     Wish-list and wish relationship. Wishes on a wish-list of a user.
#     """
#     list = models.ForeignKey(to=TodoList)
#     task = models.ForeignKey(to=Wish)
#
#     class Meta:
#         unique_together = ('list', 'task')


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


# ========== Signals ==========

@receiver(post_save, sender=UserModel)
def post_save_user(sender, **kwargs):
    user = kwargs['instance']
    created = kwargs['created']

    if created and user is not None:
        profile = UserProfile(user=user)
        profile.username = user.username
        profile.save()
        TodoList.init_data(profile)
        WishList.init_data(profile)


