#!/usr/bin/env python
# coding: utf-8

"""
Social account related models
"""
from django.db import models
from django.templatetags.static import static
from django.utils import timezone
from .common import ProfileBasedModel
from .consts import SocialPlatform


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