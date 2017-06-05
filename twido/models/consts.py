#!/usr/bin/env python
# coding: utf-8


"""
Constants definitions
"""

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.templatetags.static import static


class SocialPlatform(object):
    """
    Constants and choice for social platforms.
    """
    TWITTER = 'TW'
    FACEBOOK = 'FB'
    WEIBO = 'WB'
    _texts = {
        TWITTER: _('Twitter'),
        FACEBOOK: _('Facebook'),
        WEIBO: _('Weibo'),
    }
    Choices = _texts.items()

    @classmethod
    def get_text(cls, code):
        return cls._texts[code]


class Gender(object):
    """
    Constants and choice for gender
    """
    MALE = 'M'
    FEMALE = 'F'
    NEITHER = 'N'
    PRIVATE = 'P'
    _texts = {
        MALE: _('Male'),
        FEMALE: _('Female'),
        NEITHER: pgettext_lazy('gender', 'Neither'),
        PRIVATE: pgettext_lazy('gender', 'Private'),
    }
    _icons = {
        MALE: 'flaticon-man-with-short-hair-profile-avatar',
        FEMALE: 'flaticon-woman-with-dark-long-hair-avatar',
        NEITHER: 'flaticon-avatar-of-a-person-with-dark-short-hair',
        PRIVATE: 'flaticon-personal-profile-image',
    }
    _imgs = {
        MALE: static('twido/img/avatar-man.png'),
        FEMALE: static('twido/img/avatar-woman.png'),
        NEITHER: static('twido/img/avatar-neither.png'),
        PRIVATE: static('twido/img/avatar-private.png'),
    }
    _texts_and_icons = []
    _texts_and_imgs = []
    Choices = _texts.items()
    Icons = _icons.items()
    Texts = _texts.items()
    Images = _imgs.items()

    @classmethod
    def get_texts_and_icons(cls):
        if cls._texts_and_icons:
            return cls._texts_and_icons

        rc = []
        for k, v in cls._texts.items():
            rc.append((k, {'text': v, 'icon': cls._icons.get(k)}))
        cls._texts_and_icons = sorted(rc)
        return cls._texts_and_icons

    @classmethod
    def get_texts_and_imgs(cls):
        if cls._texts_and_imgs:
            return cls._texts_and_imgs

        rc = []
        for k, v in cls._texts.items():
            rc.append((k, {'text': v, 'img': cls._imgs.get(k)}))
        cls._texts_and_imgs = sorted(rc)
        return cls._texts_and_imgs

    @classmethod
    def get_text(cls, code):
        return cls._texts[code]

    @classmethod
    def get_icon(cls, code):
        return cls._icons[code]

    @classmethod
    def get_img(cls, code):
        return cls._imgs[code]


class TaskStatus(object):
    NEW = 0
    STARTED = 1
    PAUSED = 2
    DONE = 9
    EXPIRED = 10
    CANCEL = -1
    _texts = {
        NEW: _('New'),
        STARTED: _('Started'),
        PAUSED: _('Paused'),
        DONE: _('Done'),
        CANCEL: _('Cancelled'),
        EXPIRED: _('Expired'),
    }
    _glyphicons = {
        NEW: 'glyphicon glyphicon-record text-primary ',
        STARTED: 'glyphicon glyphicon-play text-info',
        PAUSED: 'glyphicon glyphicon-pause text-default',
        DONE: 'glyphicon glyphicon-ok text-success',
        CANCEL: 'glyphicon glyphicon-remove text-muted',
        EXPIRED: 'glyphicon glyphicon-exclamation-sign text-danger',
    }
    Choices = _texts.items()
    GlyphIcons = _glyphicons.items()

    @classmethod
    def get_text(cls, status):
        assert -1 <= status <= 10
        return cls._texts[status]

    @classmethod
    def get_glyphicon(cls, status):
        assert -1 <= status <= 10
        return cls._glyphicons[status]
