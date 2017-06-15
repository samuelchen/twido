#!/usr/bin/env python
# coding: utf-8

"""
Twitter related
"""
import tweepy
from requests_oauthlib import OAuth1Session


class TwitterClientManager(object):

    @classmethod
    def create_oauth_handler(cls, consumer_key, consumer_secret, callback=None, proxy=''):
        return TweepyOAuthHandler(consumer_key=consumer_key, consumer_secret=consumer_secret,
                                  callback=callback, proxy=proxy)

    @classmethod
    def create_api_client(cls, oauth_handler, access_token, access_token_secret, proxy=''):
        auth = oauth_handler
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, proxy=proxy)
        return api

    TweepError = tweepy.TweepError


class TweepyOAuthHandler(tweepy.OAuthHandler):
    """
    Replacement for tweepy OAuthHandler to enable proxy for Twitter oAuth
    """

    def __init__(self, consumer_key, consumer_secret, callback=None, proxy=''):
        super(TweepyOAuthHandler, self).__init__(consumer_key=consumer_key,
                                                 consumer_secret=consumer_secret,
                                                 callback=callback)
        self.proxy = proxy
        self.proxies = {
            'https': self.proxy,
            'http': self.proxy
        }

    def _get_request_token(self, access_type=None):
        try:
            url = self._get_oauth_url('request_token')
            if access_type:
                url += '?x_auth_access_type=%s' % access_type
            return self.oauth.fetch_request_token(url, proxies=self.proxies)
        except Exception as e:
            # TODO: handle bad authorization exception (config.ini not set)
            # Error: Token request failed with code 400, response was '{"errors":[{"code":215,"message":"Bad Authentication data."}]}'.
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
            resp = self.oauth.fetch_access_token(url, proxies=self.proxies)
            self.access_token = resp['oauth_token']
            self.access_token_secret = resp['oauth_token_secret']
            return self.access_token, self.access_token_secret
        except Exception as e:
            raise tweepy.TweepError(e)
