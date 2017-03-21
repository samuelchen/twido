#!/usr/bin/env python
# coding: utf-8

from twido.models import RawTweet, Config
from pyutils.langutil import MutableEnum
import abc
import tweepy
import time
import simplejson as json
import os
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


class Spider(object):
    """
    Abstract base class for all spiders.
    """
    __metaclass__ = abc.ABCMeta

    __data_folder = './data'    # storage folder if storage type is FILE
    __last_id_entry_name = 'tweets_last_id'

    def __init__(self, storage=StorageType.DB):
        """
        Initial spider with given storage type.
        :param storage:
        :return:
        """
        self._storage = storage

    def save_entry(self, entry):
        """
        save an entry
        :param entry: tweet/status entry
        :return:
        """
        tweet = entry

        if StorageType.has_DB(self._storage):
            tw = RawTweet()
            tw.id = tweet.id
            tw.created_at = tweet.created_at
            tw.user = tweet.user.screen_name
            tw.text = tweet.text
            tw.raw = json.dumps(tweet._json)
            tw.save()

        if StorageType.has_FILE(self._storage):
            name = str(tweet.id)
            subfolder = name[:4]

            path = os.path.join(self.__data_folder, subfolder)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                log.debug('Created folder %s' % path)

            path = os.path.join(self.__data_folder, subfolder, name) + '.json'

            with open(path, 'wt', encoding='utf-8') as f:
                t = json.dumps(tweet._json, indent=2)
                f.write(t)

        if StorageType.has_NONE(self._storage):
            raise ValueError('%s is not valid combination of storage types.' % self._storage)

        last_id = str(tweet.id)
        log.debug('\t%d [%s] *%d <%s> "%s" %s' % (tweet.id, tweet.created_at, tweet.favorite_count,
                                                  tweet.lang, tweet.user.screen_name, tweet.text))

        return last_id

    def save_last_id(self, last_id):
        """
        save last fetched entry id
        :return:
        """

        if StorageType.has_DB(self._storage):
            opt, created = Config.objects.get_or_create(name=self.__last_id_entry_name)
            opt.value = last_id
            opt.save()

        if StorageType.has_FILE(self._storage):
            path = os.path.join(self.__data_folder, self.__last_id_entry_name)
            with open(path, 'wt', encoding='utf-8') as f:
                f.write(last_id)

        if StorageType.has_NONE(self._storage):
            raise ValueError('%s is not valid combination of storage types.' % self._storage)

    def get_last_id(self):
        """
        obtain last fetched entry id
        :return:
        """
        last_id = '0'
        path = os.path.join(self.__data_folder, self.__last_id_entry_name)
        if StorageType.has_DB(self._storage):
            opt, created = Config.objects.get_or_create(name=self.__last_id_entry_name)
            if created:
                opt.value = last_id
                opt.save()
            else:
                last_id = opt.value
        if StorageType.has_FILE(self._storage):
            try:
                with open(path, 'rt', encoding='utf-8') as f:
                    last_id = f.readline()
            except FileNotFoundError:
                pass

        if StorageType.has_NONE(self._storage):
            raise ValueError('%s is not valid combination of storage types.' % self._storage)

        return last_id

    @abc.abstractmethod
    def fetch(self):
        """
        Fetch entries
        :return:
        """
        pass


class TwitterSpider(Spider):
    def __init__(self, consumer_key, consumer_secret,
                 access_token, access_token_secret,
                 storage=StorageType.DB, proxy=''):
        super(TwitterSpider, self).__init__(storage=storage)
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth, proxy=proxy or '')

    def _limit_handled(self, cursor):
        while True:
            try:
                yield cursor.next()
            except tweepy.RateLimitError:
                dur = 15 * 60
                log.debug('Reaches rate limitation. Waiting %d seconds ...' % dur)
                time.sleep(dur)

    def fetch(self):
        last_id = self.get_last_id()

        log.debug('last_id = %s' % last_id)
        cursor = tweepy.Cursor(self.api.search, q='#todo', lang='en', since_id=last_id).items()
        for tweet in self._limit_handled(cursor):
            last_id = self.save_entry(tweet)

        self.save_last_id(last_id)
