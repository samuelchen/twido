#!/usr/bin/env python
# coding: utf-8


"""
Spider and parser related models
"""

from django.db import models
from django.utils import timezone
from .consts import SocialPlatform


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
