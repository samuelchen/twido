#!/usr/bin/env python
# coding: utf-8

"""
Module to parse a tweets/status
"""

from twido.models import RawStatus, SocialPlatform
from twido.models import UserProfile
from twido.models import Todo, Wish, TodoList, WishList
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

    def __init__(self, endpoint, storage=StorageType.DB):
        super(Parser, self).__init__(storage=storage)
        self._endpoint = endpoint

    def parse_status(self, status_json):

        status_obj = MutableEnum(json.loads(status_json))
        status_obj.user = MutableEnum(status_obj.user)
        status_obj._json = status_json

        log.info('Parsing %s' % status_obj.id_str)

        profile = self._parse_user(status_obj.user)
        return self._parse_task(status_obj, profile)

    def _parse_user(self, user_obj):
        """
        Generate fake user profile from status user information
        :param user_obj:
        :return: instance of FakeUserProfile model
        """
        user = user_obj
        # u, created = UserModel.objects.get_or_create(username=user.screen_name)
        # if created:
        #     u.is_active = False
        #     u.email = u.email
        #     u.save()
        p, created = UserProfile.objects.get_or_create(username=user.screen_name)
        if created:
            p.username = user.screen_name
            p.name = user.name
            p.timezone = user.time_zone
            p.location = user.location
            p.lang = user.lang
            p.utc_offset = user.utc_offset or 0
            p.img_url = user.profile_image_url
            assert p.is_faked
            p.save()

        return p

    def _parse_task(self, status_obj, profile):
        """

        :param status_obj:
        :param profile:
        :return:
        """
        obj = status_obj

        try:
            status = RawStatus.objects.get(rawid=obj.id_str)
            log.debug('Read status %s' % status)
        except RawStatus.DoesNotExist:
            status = self.generate_status(status_obj)
            status.save()
            log.debug('Created status %s' % status)

        try:
            text, succeed = self._parse_text(obj.text, obj.created_at)
            if not succeed:
                log.error('FAILED. %s. %s' % (status, text))
                return False
        except requests.exceptions.ConnectionError as err:
            log.error('CONNECTION lost. %s. %s' % (status, err))
            return False

        try:
            if obj.text.find('#todo') > 0:
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
                task.list = TodoList.get_default(profile)
                task.save()
            elif obj.text.find('#wish') > 0:
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
                task.list = WishList.get_default(profile)
                task.save()
            else:
                log.info('IGNORED due to no hash tags. %s' % status)
        except IntegrityError as err:
            log.error('IGNORED due to duplicated. %s. Error:%s' % (status, err))

        finally:
            if StorageType.contains_DB(self.storage):
                status.parsed = True
                status.save()

        return True

    def _parse_text(self, text, dt):

        payload = {
            'text': text,
            'date': dt
        }
        r = requests.get(self._endpoint, params=payload)
        log.debug('HTTP status code: %d' % r.status_code)
        # log.debug(r.text)

        succeed = False
        if r.text.startswith('error:'):
            succeed = False
        elif 200 <= r.status_code < 300:
            succeed = True
        else:
            succeed = False
        return r.text, succeed

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
                    # p = os.path.join(self.data_folder, sub, file)
                    # os.rename(p, p[:-7])
                    if file > name and not file.endswith('parsed'):
                        path = os.path.join(self.data_folder, sub, file)
                        status_json = open(path, 'rt', encoding='utf-8').read()
                        if self.parse_status(status_json):
                            os.rename(path, path + '.parsed')
                    id_str = name[:-5]
                    if last_id < id_str:
                        last_id = id_str
                    name = file

        else:
            raise ValueError('Unsupported storage type %s' % self.storage)

        self.save_last_id(last_id)
        log.info('Parsing done (last_id=%s).' % last_id)