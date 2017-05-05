#!/usr/bin/env python
# coding: utf-8

from twido.models import SocialPlatform
from .storage import StorageType, StorageMixin
from .import weibo


import abc
import tweepy
import time
import logging
log = logging.getLogger(__name__)


class Spider(StorageMixin):
    """
    Abstract base class for all spiders.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def fetch(self, test=False, limited=0):
        """
        Fetch statuses
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

    @property
    def social_platform(self):
        return SocialPlatform.TWITTER

    def fetch(self, test=False, limited=0):
        last_id = self.get_last_id()
        count = 0

        log.debug('last_id = %s' % last_id)
        cursor = tweepy.Cursor(self.api.search, lang='en',
                               q='#todo list:samuelchen/tester' if test else '#todo',
                               since_id=last_id).items()
        for tweet in self._limit_handled(cursor):
            status = self.generate_status(tweet)
            self.save_status(status)
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

    # def generate_status(self, raw_obj):
    #     """
    #     Generate status model instance from raw status object (such as a tweet object)
    #     :param raw_obj: The status object from SDK or REST API
    #     :return: an instance of RawStatus.
    #     """
    #     tweet = raw_obj
    #     status = RawStatus()
    #     status.source = self.social_platform
    #     status.rawid = tweet.id_str
    #     status.created_at = tweet.created_at.replace(tzinfo=utc)
    #     status.username = tweet.user.screen_name
    #     status.text = tweet.text
    #     status.raw = json.dumps(tweet._json, indent=2)
    #     return status


class WeiboSpider(Spider):

    def __init__(self, app_key, app_secret,
                 storage=StorageType.DB, proxy=''):
        super(WeiboSpider, self).__init__(storage=storage)
        # self.api = weibo.APIClient(app_key=app_key, app_secret=app_secret, redirect_uri=CALLBACK_URL)
        # self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        # self.auth.set_access_token(access_token, access_token_secret)
        # self.api = tweepy.API(self.auth, proxy=proxy or '')


