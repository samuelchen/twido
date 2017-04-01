#!/usr/bin/env python
# coding: utf-8

from twido.models import RawTweet
from django.utils.timezone import utc
import abc
import tweepy
import time
import simplejson as json
from .storage import StorageType, StorageMixin
import logging
log = logging.getLogger(__name__)


class Spider(StorageMixin):
    """
    Abstract base class for all spiders.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def fetch(self):
        """
        Fetch entries
        :return: N/A
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
                dur = 900   # 15 * 60
                log.debug('Reaches rate limitation. Waiting %d seconds ...' % dur)
                time.sleep(dur)

    # overrides abstract methods
    def generate_entry(self, raw_obj):

        tweet = raw_obj
        entry = RawTweet()
        entry.rawid = tweet.id_str
        entry.created_at = tweet.created_at.replace(tzinfo=utc)
        entry.username = tweet.user.screen_name
        entry.text = tweet.text
        entry.raw = json.dumps(tweet._json, indent=2)
        return entry

    def fetch(self, limited=0):
        last_id = self.get_last_id()
        count = 0

        log.debug('last_id = %s' % last_id)
        cursor = tweepy.Cursor(self.api.search, q='#todo', lang='en', since_id=last_id).items()
        for tweet in self._limit_handled(cursor):
            self.save_entry(tweet)
            # TODO: last_id logic needs to be clear. (tweepy result-set is not sorted)
            if last_id < tweet.id_str:
                last_id = tweet.id_str

            if limited > 0:
                count += 1
                if count == limited:
                    break

            log.debug('\t%d [%s] *%d <%s> "%s" %s' % (tweet.id, tweet.created_at, tweet.favorite_count,
                                                      tweet.lang, tweet.user.screen_name, tweet.text))

        self.save_last_id(last_id)
        log.debug('last_id saved (%s)' % last_id)
