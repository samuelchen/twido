#!/usr/bin/env python
# coding: utf-8

"""
Utilities
"""

import configparser
from pyutils.langutil import MutableEnum
import tweepy
from requests_oauthlib import OAuth1Session
from django.conf import settings


def load_config(config_file):
    options = MutableEnum()
    parser = configparser.ConfigParser()
    read_ok_list = parser.read(config_file)
    if config_file in read_ok_list:
        for section in parser.sections():
            sec = MutableEnum()
            for k, v in parser.items(section):
                sec[k] = v
            options[section] = sec
    else:
        raise IOError('Fail to access %s' % config_file)
    return options


from email.utils import parsedate
from datetime import datetime


def parse_datetime(string):
    return datetime(*(parsedate(string)[:6]))


def send_reg_email(email, id, name=None):
    folder = './data/email/'
    path = folder + email + '.html'
    if not name:
        name = email
    content = '''
    <html>
    <head>
        <title>Welcome to register My Wish List 2</title>
    </head>
    <body>
        <H2>Welcome registering, %s</H2>
        <p>Please click the following address to confirm registration.<p>
        <a href="http://localhost:8000/reg_confirm">confirm user %s registration.</a>
    </body>
    ''' % (name, id)
    with open(path, 'wt') as f:
        f.write(content)


class TwitterClientManager(object):

    cfg = load_config(settings.CONFIG_FILE)

    @classmethod
    def create_oauth_handler(cls, callback=None):
        return TweepyOAuthHandler(callback=callback)

    @classmethod
    def create_api_client(cls, access_token, access_token_secret):
        auth = cls.create_oauth_handler()
        # auth = tweepy.OAuthHandler(consumer_key=cls.cfg.twitter.consumer_key,
        #                            consumer_secret=cls.cfg.twitter.consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, proxy=cls.cfg.common.proxy or '')
        return api


class TweepyOAuthHandler(tweepy.OAuthHandler):
    """
    Replacement for tweepy OAuthHandler to enable proxy for Twitter oAuth
    """

    def __init__(self, callback=None):
        self.cfg = load_config(settings.CONFIG_FILE)
        super(TweepyOAuthHandler, self).__init__(consumer_key=self.cfg.twitter.consumer_key,
                                                 consumer_secret=self.cfg.twitter.consumer_secret,
                                                 callback=callback)

    def _get_request_token(self, access_type=None):
        try:
            url = self._get_oauth_url('request_token')
            if access_type:
                url += '?x_auth_access_type=%s' % access_type
            proxies = {
                'https': self.cfg.common.proxy,
                'http': self.cfg.common.proxy
            }
            return self.oauth.fetch_request_token(url, proxies=proxies)
        except Exception as e:
            raise tweepy.TweepError(e)

    def get_access_token(self, verifier=None):
        """
        After user has authorized the request token, get access token
        with user supplied verifier.
        """
        try:
            url = self._get_oauth_url('access_token')
            self.oauth = OAuth1Session(self.consumer_key,
                                       client_secret=self.consumer_secret,
                                       resource_owner_key=self.request_token['oauth_token'],
                                       resource_owner_secret=self.request_token['oauth_token_secret'],
                                       verifier=verifier, callback_uri=self.callback)
            proxies = {
                'https': self.cfg.common.proxy,
                'http': self.cfg.common.proxy
            }
            resp = self.oauth.fetch_access_token(url, proxies=proxies)
            self.access_token = resp['oauth_token']
            self.access_token_secret = resp['oauth_token_secret']
            return self.access_token, self.access_token_secret
        except Exception as e:
            raise tweepy.TweepError(e)
