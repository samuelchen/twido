#!/usr/bin/env python
# coding: utf-8

"""
Module to parse a tweets/status
"""

import abc
from twido.models import RawTweet, Config
from .storage import StorageType, StorageMixin
import os
import simplejson as json
import requests
import logging
log = logging.getLogger(__name__)


class Parser(StorageMixin):
    """
    Abstract base class for parsing social message entry
    """
    __metaclass__ = abc.ABCMeta

    def parse_entry(self, entry):
        text = None
        dt = None
        if StorageType.has_DB(self.storage):
            print(entry.id, entry.username, entry.text)
            text = entry.text
            dt = entry.created_at
        elif StorageType.has_FILE(self.storage):
            tweet = json.loads(entry)
            text = tweet['text']
            dt = tweet['created_at']
            print(tweet['id'], tweet['user']['screen_name'], tweet['text'])

        payload = {
            'text': text,
            'date': dt
        }
        r = requests.get('http://127.0.0.1:8080/parse', params=payload)
        print(r.status_code, r.text)
        # print(dateparser.parse(text), ' : ', text)

    @abc.abstractmethod
    def parse(self):
        pass


class TwitterParser(Parser):

    def parse(self):
        last_id = self.get_last_id()
        log.debug('last_id = %s' % last_id)
        if StorageType.has_DB(self.storage):
            for tweet in RawTweet.objects.filter(id__gt=int(last_id)).order_by('id').iterator():
                self.parse_entry(tweet)
                id_str = str(tweet.id)
                if last_id < id_str:
                    last_id = id_str
        elif StorageType.has_FILE(self.storage):

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
                    entry = open(path, 'rt', encoding='utf-8').read()
                    self.parse_entry(entry)
                    name = file
                    id_str = name[:-5]
                    if last_id < id_str:
                        last_id = id_str
        self.save_last_id(last_id)
