#!/usr/bin/env python
# coding: utf-8


class SocialPlatform(object):
    """
    Constants and choice for social platforms.
    """
    TWITTER = 'TW'
    FACEBOOK = 'FB'
    WEIBO = 'WB'
    SocialAccountChoices = (
        (TWITTER, 'Twitter'),
        (FACEBOOK, 'Facebook'),
        (WEIBO, 'Weibo'),
    )