#!/usr/bin/env python
# coding: utf-8

"""
Module to parse a tweets/status
"""

from twido.models import RawStatus, SocialPlatform
from twido.models import UserProfile, UserModel
from twido.models import Todo, Wish
from .storage import StorageType, StorageMixin
from pyutils.langutil import MutableEnum
from twido.utils import parse_datetime
from django.utils.timezone import utc
from django.db.utils import IntegrityError


import abc
import os
import simplejson as json
import requests
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import logging
log = logging.getLogger(__name__)


class Parser(StorageMixin):
    """
    Abstract base class for parsing social status
    """
    __metaclass__ = abc.ABCMeta

    def parse_status(self, status_json):

        status_obj = MutableEnum(json.loads(status_json))
        status_obj.user = MutableEnum(status_obj.user)
        status_obj._json = status_json

        log.info('Parsing %s' % status_obj.id_str)

        user, profile = self._parse_user(status_obj.user)
        self._parse_task(status_obj, profile)

    def _parse_user(self, user_obj):
        user = user_obj
        u, created = UserModel.objects.get_or_create(username=user.screen_name)
        if created:
            u.is_active = False
            u.email = u.email
            u.save()
        p, created = UserProfile.objects.get_or_create(user=u)
        if created:
            p.name = user.name
            p.timezone = user.time_zone
            p.location = user.location
            p.lang = user.lang
            p.utc_offset = user.utc_offset or 0
            p.img_url = user.profile_image_url
            p.save()

        return u, p

    def _parse_task(self, status_obj, profile):
        obj = status_obj

        try:
            status = RawStatus.objects.get(rawid=obj.id_str)
            log.debug('Read status id=%d rawid=%s' % (status.id, status.rawid))
        except RawStatus.DoesNotExist:
            status = self.generate_status(status_obj)
            status.save()
            log.debug('Created status id=%d rawid=%s' % (status.id, status.rawid))

        try:
            text = self._parse_text(obj.text, obj.created_at)
        except requests.exceptions.ConnectionError as err:
            log.error('Text parsing service connection error. %s' % err)
            return

        try:
            if obj.text.find('#todo'):
                task = Todo()
                task.profile = profile
                task.status = status
                if isinstance(obj.created_at, str):
                    task.created_at = parse_datetime(obj.created_at).replace(tzinfo=utc)
                else:
                    task.created_at = obj.created_at.replace(tzinfo=utc)
                task.title = obj.text
                task.text = obj.text
                task.content = text
                task.deadline = None
                task.save()
            elif text.find('#wish'):
                task = Wish()
                task.profile = profile
                task.status = status
                if isinstance(obj.created_at, str):
                    task.created_at = parse_datetime(obj.created_at).replace(tzinfo=utc)
                else:
                    task.created_at = obj.created_at.replace(tzinfo=utc)
                task.title = obj.text
                task.text = obj.text
                task.content = text
                task.save()
            else:
                log.info('Ignore @%s "%s"' % (obj.user.screen_name, text))
        except IntegrityError as err:
            log.error('Ignore status(id=%d rawid=%s) @%s "%s". Error:%s' % (
            status.id, status.rawid, obj.user.screen_name, text, err))

        finally:
            if StorageType.contains_DB(self.storage):
                status.parsed = True
                status.save()

    def _parse_text(self, text, dt):

        payload = {
            'text': text,
            'date': dt
        }
        r = requests.get('http://127.0.0.1:8080/parse', params=payload)
        # log.debug(r.status_code)
        # log.debug(r.text)
        return r.text

    @abc.abstractmethod
    def parse(self):
        """
        Parse all status from last id.
        Create user if not existing.
        Create record and save into Todo model.
        :return:
        """
        pass


class TwitterParser(Parser):

    @property
    def social_platform(self):
        return SocialPlatform.TWITTER

    def parse(self):

        last_id = self.get_last_id()
        log.info('Start parsing (last_id=%s) ...' % last_id)

        if StorageType.contains_DB(self.storage):

            for status in RawStatus.objects.filter(id__gt=int(last_id), parsed=False).order_by('id').iterator():
                self.parse_status(status.raw)
                id_str = str(status.id)
                if last_id < id_str:
                    last_id = id_str

        elif StorageType.contains_FILE(self.storage):

            subfolders = sorted(os.listdir(self.data_folder))
            name = '%s.json' % last_id

            for sub in subfolders:
                path = os.path.join(self.data_folder, sub)
                if not os.path.isdir(path):
                    continue
                files = sorted(os.listdir(path))
                for file in files:
                    if file <= name:
                        continue
                    path = os.path.join(self.data_folder, sub, file)
                    status_json = open(path, 'rt', encoding='utf-8').read()
                    self.parse_status(status_json)
                    name = file
                    id_str = name[:-5]

                    if last_id < id_str:
                        last_id = id_str
        else:
            pass

        self.save_last_id(last_id)
        log.info('Parsing done (last_id=%s).' % last_id)