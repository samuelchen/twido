#!/usr/bin/env python
# coding: utf-8

from twido.models import Config, RawStatus
from django.utils.timezone import utc
from django.db.utils import IntegrityError
from pyutils.langutil import MutableEnum
from twido.utils import parse_datetime

import simplejson as json
import os
import abc
import logging
log = logging.getLogger(__name__)


# storage type enums and checker methods.
StorageType = MutableEnum(
    DB=1,
    FILE=2,
)
StorageType.contains_FILE = lambda t: StorageType.FILE & t > 0
StorageType.contains_DB = lambda t: StorageType.DB & t > 0
StorageType.contains_NONE = lambda t: not(StorageType.contains_FILE(t) or StorageType.contains_DB(t))


class StorageMixin(object):

    __metaclass__ = abc.ABCMeta

    __data_folder = './data'    # storage folder if storage type is FILE
    __last_id_entry_prefix = 'last_id_'

    def __init__(self, storage=StorageType.DB):
        """
        Initial with given storage type.
        :param storage:
        :return:
        """
        self.__storage = storage
        log.info('Storage Tpye : DB(%s) FILE(%s)' % (
            bool(StorageType.contains_DB(self.__storage)),
            bool(StorageType.contains_FILE(self.__storage))
        ))

    @property
    def storage(self):
        return self.__storage

    @property
    def data_folder(self):
        return self.__data_folder + '/' + self.social_platform

    @property
    def last_id_config_key(self):
        return self.__last_id_entry_prefix + self.__class__.__name__

    @staticmethod
    def get_sub_folder(rawid):
        return str(rawid)[:4]

    def save_last_id(self, last_id):
        """
        save last entry id
        :return:
        """

        if StorageType.contains_DB(self.storage):
            opt, created = Config.get_or_create_sys_conf(name=self.last_id_config_key)
            opt.value = last_id
            opt.save()

        elif StorageType.contains_FILE(self.storage):
            path = os.path.join(self.data_folder, self.last_id_config_key)
            with open(path, 'wt', encoding='utf-8') as f:
                f.write(last_id)

        else:
            raise ValueError('%s is not valid combination of storage types.' % self.storage)

    def get_last_id(self):
        """
        obtain last fetched entry id
        :return:
        """
        last_id = '0'
        if StorageType.contains_DB(self.storage):
            opt, created = Config.get_or_create_sys_conf(name=self.last_id_config_key)
            if created:
                opt.value = last_id
                opt.save()
            else:
                last_id = opt.value         # str
        elif StorageType.contains_FILE(self.storage):
            path = os.path.join(self.data_folder, self.last_id_config_key)
            try:
                with open(path, 'rt', encoding='utf-8') as f:
                    last_id = f.readline()  # str
            except FileNotFoundError:
                pass

        else:
            raise ValueError('%s is not valid combination of storage types.' % self.storage)

        return last_id

    def save_status(self, status):
        """
        Save a status into database
        :param status: raw status object (RawStatus model entity)
        :return: N/A
        """

        if StorageType.contains_NONE(self.storage):
            raise ValueError('%s is not valid combination of storage types.' % self.storage)

        if StorageType.contains_DB(self.storage):
            try:
                status.save()
            except IntegrityError:
                log.error('Entry "%s" is already existed.' % status.rawid)

        if StorageType.contains_FILE(self.storage):
            name = status.rawid
            subfolder = self.get_sub_folder(name)

            path = os.path.join(self.data_folder, subfolder)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                log.debug('Created folder %s' % path)

            path = os.path.join(self.data_folder, subfolder, name) + '.json'
            path_parsed = path + '.parsed'

            if os.path.exists(path_parsed):
                path = path_parsed
            with open(path, 'wt', encoding='utf-8') as f:
                t = status.raw
                f.write(t)

    def generate_status(self, raw_obj):
        """
        Generate status model instance from raw status object (such as a tweet object)
        :param raw_obj: The status object from SDK or REST API
        :return: an instance of RawStatus.
        """
        tweet = raw_obj
        status = RawStatus()
        status.source = self.social_platform
        status.rawid = tweet.id_str
        if isinstance(tweet.created_at, str):
            status.created_at = parse_datetime(tweet.created_at).replace(tzinfo=utc)
        else:
            status.created_at = tweet.created_at.replace(tzinfo=utc)
        status.username = tweet.user.screen_name
        status.text = tweet.text
        status.raw = json.dumps(tweet._json, ensure_ascii=False, indent=2)
        return status

    @abc.abstractproperty
    def social_platform(self):
        """
        abstract property to tell which social platform
        :return: social platform code name. (from model.SocialPlatform)
        """
        pass
