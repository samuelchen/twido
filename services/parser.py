#!/usr/bin/env python
# coding: utf-8

"""
Module to parse a tweets/status
"""
from django.db import transaction
from pyutils.json import to_serializable

from twido.models import RawStatus, SocialPlatform, Visibility
from twido.models import SocialAccount, UserProfile
from twido.models import Task, List
from twido.models.task import TaskMeta
from twido.parser import Timex3Parser

from .storage import StorageType, StorageMixin
from pyutils.langutil import MutableEnum
from twido.utils import parse_datetime
from django.utils.timezone import utc
from django.db.utils import IntegrityError

import abc
import os
import re
import simplejson as json
import requests
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import logging
log = logging.getLogger(__name__)

re_hashtag = re.compile(r'(?P<hash>#(todo|wish))(\s|\Z)', re.IGNORECASE + re.MULTILINE)


def test_re():
    m = re_hashtag.search('''#Looking for something #todo while in #LasVegas
    #partybus #trucklimo #limo #SUV #reserve one and have a
    #goodtime https://t.co/qlBi4BAcXF''')
    print(m)
    print(m.groupdict()['hash'] if m else None)
    print(m.group(0))
    print(m.group(1))

    m = re_hashtag.search('''#toDO RT HacksterPro... while in #LasVegas
    #partybus #trucklimo #limo #SUV #reserve one and have a
    #goodtime https://t.co/qlBi4BAcXF''')
    print(m)
    print(m.groups() if m else None)

    m = re_hashtag.search('''HacksterPro... while in #LasVegas
    #partybus #trucklimo #limo #SUV #reserve one and have a
    #goodtime https://t.co/qlBi4BAcXF blabla#WISH''')
    print(m)
    print(m.groups() if m else None)

    m = re_hashtag.search('''HacksterPro... while in #LasVegas
    #partybus #trucklimo #limo #SUV #reserve #WISHME one and have a
    #goodtime https://t.co/qlBi4BAcXF blabla''')
    print(m)
    print(m.groups() if m else None)

# test_re()
# exit(0)


class Parser(StorageMixin):
    """
    Abstract base class for parsing social status
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, endpoint, storage=StorageType.DB):
        super(Parser, self).__init__(storage=storage)
        self._endpoint = endpoint

    def parse_status(self, status_json):

        # TODO: user bulk_create to batch create tasks.
        # TODO: add commit=False arguments to speicify wether save.
        # TODO: storage "parsed" commitment moves out

        status_obj = MutableEnum(json.loads(status_json))
        status_obj.user = MutableEnum(status_obj.user)
        status_obj._json = status_json

        log.debug('Parsing %s' % status_obj.id_str)

        acc = self._parse_social_account(status_obj.user)
        return self._parse_task(status_obj, acc)

    def _parse_social_account(self, user_obj):
        """
        Generate Social account from status user information
        :param user_obj:
        :return: instance of SocialAccount model
        """
        user = user_obj
        try:
            acc = SocialAccount.objects.get(account=user.screen_name)
        except SocialAccount.DoesNotExist:
            acc = SocialAccount()
            acc.profile = UserProfile.get_sys_profile()
            acc.account = user.screen_name
            acc.name = user.name
            acc.rawid = user.id_str
            if isinstance(user.created_at, str):
                acc.created_at = parse_datetime(user.created_at).replace(tzinfo=utc)
            else:
                acc.created_at = user.created_at.replace(tzinfo=utc)

            acc.timezone = user.time_zone
            acc.location = user.location
            acc.lang = user.lang
            acc.utc_offset = user.utc_offset or 0
            acc.img_url = user.profile_image_url
            acc.img_url_https = user.profile_image_url_https

            acc.followers_count = user.followers_count
            # acc.followings_count = user.followings_count
            acc.favorites_count = user.favourites_count
            acc.statuses_count = user.statuses_count
            acc.friends_count = user.friends_count
            acc.listed_count = user.listed_count

            acc.save()

        return acc

    def _parse_task(self, status_obj, social_account):
        """

        :param status_obj:
        :param social_account:
        :return:
        """
        obj = status_obj
        acc = social_account

        try:
            status = RawStatus.objects.get(rawid=obj.id_str)
            log.debug('Read status %s' % status)
        except RawStatus.DoesNotExist:
            status = self.generate_status(status_obj)
            status.save()
            log.debug('Created status %s' % status)

        try:
            xml, succeed = self._parse_text(obj.text, obj.created_at)
            if not succeed:
                log.error('FAILED. %s. %s' % (status, xml))
                return False
        except requests.exceptions.ConnectionError as err:
            log.error('CONNECTION lost. %s. %s' % (status, err))
            return False

        # TODO: parse in a thread/process
        try:
            meta = TaskMeta()
            valid_tags = {'todo', 'wish'}
            tags = Timex3Parser.parse_hash_tags(obj.text)
            if valid_tags & set(tags):

                task = Task()
                task.list = List.get_default(acc.profile)
                task.deadline = None
                task.profile = acc.profile
                task.social_account = acc
                task.raw = status
                if isinstance(obj.created_at, str):
                    task.created_at = parse_datetime(obj.created_at).replace(tzinfo=utc)
                else:
                    task.created_at = obj.created_at.replace(tzinfo=utc)
                task.title = obj.text
                task.text = ''
                task.visibility = Visibility.PUBLIC     # public if from social platform
                task.labels = ','.join(tags)

                meta.tags = json.dumps(tags, indent=2)
                meta.dates = json.dumps(Timex3Parser.parse_dates(xml), indent=2, default=to_serializable)
                meta.simple_text = Timex3Parser.parse_text(obj.text)
                meta.timex = xml
                with transaction.atomic():
                    task.save()
                    meta.task = task
                    meta.save()

                log.debug('SAVED task %s. (rawid: %s)' % (task, status.rawid))
            else:
                log.info('IGNORED due to no valid hash tags (%s). %s' % (valid_tags, status))

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

    def parse(self, include_parsed=False):

        last_id = self.get_last_id()
        log.info('Start parsing (last_id=%s) ...' % last_id)

        if StorageType.contains_DB(self.storage):
            filter_kwargs = {}
            if not include_parsed:
                filter_kwargs['parsed'] = False
            for status in RawStatus.objects.filter(id__gt=int(last_id), source=self.social_platform,
                                                   **filter_kwargs).order_by('id').iterator():
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
                    if file > name and (include_parsed or not file.endswith('.parsed')):
                        path = os.path.join(self.data_folder, sub, file)
                        status_json = open(path, 'rt', encoding='utf-8').read()
                        if self.parse_status(status_json):
                            if not path.endswith('.parsed'):
                                os.rename(path, path + '.parsed')
                    id_str = name[:-5]
                    if last_id < id_str:
                        last_id = id_str
                    name = file

        else:
            raise ValueError('Unsupported storage type %s' % self.storage)

        self.save_last_id(last_id)
        log.info('Parsing done (last_id=%s).' % last_id)