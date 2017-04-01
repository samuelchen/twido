#!/usr/bin/env python
# coding: utf-8

from twido.models import Config
from django.db.utils import IntegrityError
from pyutils.langutil import MutableEnum
import os
import abc
import logging
log = logging.getLogger(__name__)


# storage type enums and checker methods.
StorageType = MutableEnum(
    DB=1,
    FILE=2,
)
StorageType.has_FILE = lambda t: StorageType.FILE & t > 0
StorageType.has_DB = lambda t: StorageType.DB & t > 0
StorageType.has_NONE = lambda t: not(StorageType.has_FILE(t) or StorageType.has_DB(t))


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

    @property
    def storage(self):
        return self.__storage

    @property
    def data_folder(self):
        return self.__data_folder

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

        if StorageType.has_DB(self.storage):
            opt, created = Config.objects.get_or_create(name=self.last_id_config_key)
            opt.value = last_id
            opt.save()

        elif StorageType.has_FILE(self.storage):
            path = os.path.join(self.__data_folder, self.last_id_config_key)
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
        if StorageType.has_DB(self.storage):
            opt, created = Config.objects.get_or_create(name=self.last_id_config_key)
            if created:
                opt.value = last_id
                opt.save()
            else:
                last_id = opt.value         # str
        elif StorageType.has_FILE(self.storage):
            path = os.path.join(self.__data_folder, self.last_id_config_key)
            try:
                with open(path, 'rt', encoding='utf-8') as f:
                    last_id = f.readline()  # str
            except FileNotFoundError:
                pass

        else:
            raise ValueError('%s is not valid combination of storage types.' % self.storage)

        return last_id

    def save_entry(self, raw_obj):
        """
        save an entry
        :param raw_obj: raw object of an entry (such as a tweet object)
        :return: N/A
        """
        entry = self.generate_entry(raw_obj)
        # assert isinstance(entry, self.Entry)

        if StorageType.has_NONE(self.storage):
            raise ValueError('%s is not valid combination of storage types.' % self.storage)

        if StorageType.has_DB(self.storage):
            try:
                entry.save()
            except IntegrityError:
                log.error('Entry "%s" is already existed.' % entry.rawid)

        if StorageType.has_FILE(self.storage):
            name = entry.rawid
            subfolder = self.get_sub_folder(name)

            path = os.path.join(self.data_folder, subfolder)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                log.debug('Created folder %s' % path)

            path = os.path.join(self.data_folder, subfolder, name) + '.json'

            with open(path, 'wt', encoding='utf-8') as f:
                t = entry.raw
                f.write(t)

    @abc.abstractmethod
    def generate_entry(self, raw_obj):
        """
        Generate entry from raw entry object (such as a tweet object)
        :param raw_obj:
        :return: MUST return an instance of RawEntry or children.
        """
        pass