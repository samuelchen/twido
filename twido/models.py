#!/usr/bin/env python
# coding: utf-8

from django.db import models
from django.core.validators import validate_comma_separated_integer_list
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import AppRegistryNotReady
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
# from simple_email_confirmation.models import SimpleEmailConfirmationUserMixin
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db import transaction

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
    _texts = {
        TWITTER: _('Twitter'),
        FACEBOOK: _('Facebook'),
        WEIBO: _('Weibo'),
    }
    Choices = _texts.items()

    @classmethod
    def get_text(cls, code):
        return cls._texts[code]


class Gender(object):
    """
    Constants and choice for gender
    """
    MALE = 'M'
    FEMALE = 'F'
    NEITHER = 'N'
    PRIVATE = 'P'
    _texts = {
        MALE: _('Male'),
        FEMALE: _('Female'),
        NEITHER: _('Neither'),
        PRIVATE: _('Private'),
    }
    _icons = {
        MALE: 'flaticon-man-with-short-hair-profile-avatar',
        FEMALE: 'flaticon-woman-with-dark-long-hair-avatar',
        NEITHER: 'flaticon-avatar-of-a-person-with-dark-short-hair',
        PRIVATE: 'flaticon-personal-profile-image',
    }
    _imgs = {
        MALE: static('twido/img/avatar-man.png'),
        FEMALE: static('twido/img/avatar-woman.png'),
        NEITHER: static('twido/img/avatar-neither.png'),
        PRIVATE: static('twido/img/avatar-private.png'),
    }
    _texts_and_icons = []
    _texts_and_imgs = []
    Choices = _texts.items()
    Icons = _icons.items()
    Texts = _texts.items()
    Images = _imgs.items()

    @classmethod
    def get_texts_and_icons(cls):
        if cls._texts_and_icons:
            return cls._texts_and_icons

        rc = []
        for k, v in cls._texts.items():
            rc.append((k, {'text': v, 'icon': cls._icons.get(k)}))
        cls._texts_and_icons = sorted(rc)
        return cls._texts_and_icons

    @classmethod
    def get_texts_and_imgs(cls):
        if cls._texts_and_imgs:
            return cls._texts_and_imgs

        rc = []
        for k, v in cls._texts.items():
            rc.append((k, {'text': v, 'img': cls._imgs.get(k)}))
        cls._texts_and_imgs = sorted(rc)
        return cls._texts_and_imgs

    @classmethod
    def get_text(cls, code):
        return cls._texts[code]

    @classmethod
    def get_icon(cls, code):
        return cls._icons[code]

    @classmethod
    def get_img(cls, code):
        return cls._imgs[code]

# ------ Common Models -----


class UserProfile(models.Model):
    """
    User Profile.

    Django User is used for authorization (login/logout/register).
    User.username will always set to User.email.
    The Django User model's "email" field is useless.

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
            p.name = _('SYS')
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
        Return a display name. (never return email including user.username)
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


class SocialAccount(ProfileBasedModel):
    """
    Social accounts such as Twitter, Facebook and Weibo.
    """
    account = models.CharField(max_length=100, db_index=True)      # maybe screen_name, email or etc.
    platform = models.CharField(max_length=2, choices=SocialPlatform.Choices, default=SocialPlatform.TWITTER)
    name = models.CharField(max_length=100, null=True, blank=True)  # nick name, user.first_name/user.last_name
    tokens = models.TextField(verbose_name='Tokens JSON')
    rawid = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(editable=False)

    followers_count = models.IntegerField(default=0)
    followings_count = models.IntegerField(default=0)
    friends_count = models.IntegerField(default=0)
    statuses_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)
    listed_count = models.IntegerField(default=0)
    img_url = models.TextField(null=True, blank=True)
    img_url_https = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    lang = models.CharField(max_length=20, null=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    utc_offset = models.IntegerField(default=0)

    class Meta:
        unique_together = ('platform', 'account')

    def __str__(self):
        return '%s (id=%d)' % (self.account, self.id)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super(SocialAccount, self).save(*args, **kwargs)

    def get_name(self):
        """
        :return a display name
        """
        if self.name:
            return self.name
        return self.account

    def get_date_joined(self):
        return self.created_at

    def get_img_url(self):
        return self.img_url or static('twido/img/avatar-man.png')

# ----- Spider models -----

class RawStatus(models.Model):
    """
    Base class for all raw statuses.
    """
    id = models.BigAutoField(primary_key=True)
    rawid = models.CharField(max_length=50, db_index=True, unique=True, verbose_name='Raw ID')
    created_at = models.DateTimeField(editable=False)
    timestamp = models.DateTimeField(auto_now=True)
    username = models.CharField(max_length=100, db_index=True, verbose_name='Social Screen Name')
    text = models.TextField(verbose_name='Status Text')
    source = models.CharField(max_length=2, choices=SocialPlatform.Choices)
    parsed = models.BooleanField(default=False)
    raw = models.TextField(verbose_name='Raw Data')

    def __str__(self):
        return 'status(%s, id=%s, rawid=%s, user=%s, text="%s")' % (
            self.source, self.id, self.rawid, self.username,
            self.text if len(self.text) <= 20 else self.text[0:20] + '...')

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super(RawStatus, self).save(*args, **kwargs)


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
                                     db_index=True, verbose_name='Related Persons (comma separated)')
    text = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('profile', 'name')
        abstract = True

    __default_name = '__default__'

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
    def default(self):
        return self.get_default(self.profile)

    def get_related_profiles(self):
        return UserProfile.objects.filter(username__in=(self.related_users.split(',') or ''))

    def get_related_usernames(self):
        return self.related_users.split(',')

    @property
    def is_default(self):
        return self.name == self.__default_name

    def __str__(self):
        return "%d:%s" % (self.id, self.name)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, is_default=False):
        if not is_default and self.name.lower() == self.__default_name:
            raise AttributeError('List name can not be "%s" (reversed default name). ' % self.name)
        return super(List, self).save(force_insert=force_insert, force_update=force_update,
                                      using=using, update_fields=update_fields)


class WishList(List):
    """
    A wish list contains one or more things you want.
    """
    pass


class TodoList(List):
    """
    A Todo list contains one or more things you want to do or buy.
    """
    def delete(self, using=None, keep_parents=False):
        s = str(self)
        log.debug('deleting todo list %s' % s)
        with transaction.atomic():
            Todo.objects.filter(list=self, profile=self.profile).update(list=self.get_default(self.profile))
            log.debug('all tasks in todo list %s are moved to default list.' % s)
            super(TodoList, self).delete(using=using, keep_parents=keep_parents)
            log.info('todo list %s is deleted.' % s)


class TaskStatus(object):
    NEW = 0
    STARTED = 1
    PAUSED = 2
    DONE = 9
    EXPIRED = 10
    CANCEL = -1
    _texts = {
        NEW: _('New'),
        STARTED: _('Started'),
        PAUSED: _('Paused'),
        DONE: _('Done'),
        CANCEL: _('Cancelled'),
        EXPIRED: _('Expired'),
    }
    _glyphicons = {
        NEW: 'glyphicon glyphicon-file text-muted ',
        STARTED: 'glyphicon glyphicon-play text-info',
        PAUSED: 'glyphicon glyphicon-pause text-info',
        DONE: 'glyphicon glyphicon-ok text-success',
        CANCEL: 'glyphicon glyphicon-remove text-muted',
        EXPIRED: 'glyphicon glyphicon-exclamation-sign text-danger',
    }
    Choices = _texts.items()
    GlyphIcons = _glyphicons.items()

    @classmethod
    def get_text(cls, status):
        assert -1 <= status <= 10
        return cls._texts[status]

    @classmethod
    def get_glyphicon(cls, status):
        assert -1 <= status <= 10
        return cls._glyphicons[status]


class Task(ProfileBasedModel):
    """
    Base task model for todo, wish and schedule appointment
    """
    created_at = models.DateTimeField(editable=False)
    title = models.CharField(max_length=200)
    status = models.SmallIntegerField(choices=TaskStatus.Choices, default=TaskStatus.NEW, db_index=True)
    text = models.TextField(null=True, blank=True)
    labels = models.TextField(null=True, blank=True)

    content = models.TextField(null=True, blank=True)
    social_account = models.ForeignKey(to=SocialAccount, db_index=True, null=True, blank=True)
    raw = models.OneToOneField(to=RawStatus, null=True, blank=True)

    class Meta:
        abstract = True

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

    def __str__(self):
        return '%s (id=%d)' % (self.title, self.id)


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
    list_display = ('id', 'profile', 'name', 'value')
    list_display_links = ('id', 'name')


# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     """
#     User profile admin page
#     """
#     pass


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    """
    Admin page for configurations.
    """
    # list_display = ('__all__', )
    # list_display_links = ('id', 'name')
    pass

# ========== Signals ==========

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


# @receiver(post_save, sender=UserProfile)
# def post_save_profile(sender, **kwargs):
#     created = kwargs['created']
#
#     if created:
#         profile = kwargs['instance']
#         if profile.user is None:
#             profile.user = UserModel(email=profile.email, username=profile.email)
#             profile.user.save()
#             TodoList.init_data(profile)
#             WishList.init_data(profile)


# from .apps import TwidoAppConfig
# @receiver(post_migrate)
# def post_migrate(sender, **kwargs):
#     if sender.name == TwidoAppConfig.name:
#         UserProfile.init_data()

