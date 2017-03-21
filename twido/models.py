#!/usr/bin/env python
# coding: utf-8

from django.db import models


class RawTweet(models.Model):
    id = models.BigIntegerField(primary_key=True)
    created_at = models.DateField()
    timestamp = models.DateTimeField(auto_now=True)
    user = models.CharField(max_length=100, db_index=True)
    text = models.TextField()
    raw = models.TextField(verbose_name='Raw JSON data')


class Config(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    timestamp = models.DateTimeField(auto_now=True)
    value = models.TextField()
