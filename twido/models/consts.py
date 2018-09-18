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
    _imgs = {
        TWITTER: '',
        FACEBOOK: '',
        WEIBO: '',
    }
    _icons = {
        TWITTER: 'fa fa-twitter',
        FACEBOOK: 'fa fa-facebook',
        WEIBO: 'fa fa-weibo',
    }
    _enabled = {
        TWITTER: True,
        FACEBOOK: False,
        WEIBO: False,
    }
    Choices = _texts.items()
    _items = {}

    @classmethod
    def get_items(cls):
        if not cls._items:
            for k, v in cls._texts.items():
                cls._items[k] = {'code': k,
                                 'text': v,
                                 'icon': cls.get_icon(k),
                                 'img': cls.get_img(k),
                                 'enabled': cls.get_enabled(k),
                                 }
        return cls._items.items()

    @classmethod
    def get_text(cls, code):
        return cls._texts[code]

    @classmethod
    def get_img(cls, code):
        return cls._imgs[code]

    @classmethod
    def get_icon(cls, code):
        return cls._icons[code]

    @classmethod
    def get_enabled(cls, code):
        return cls._enabled[code]


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
    EXPIRED = 9
    DONE = 10
    CANCEL = 11
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
        CANCEL: 'glyphicon glyphicon-ban-circle text-muted',
        EXPIRED: 'glyphicon glyphicon-exclamation-sign text-danger',
    }
    Choices = _texts.items()
    GlyphIcons = _glyphicons.items()

    @classmethod
    def get_text(cls, status):
        assert TaskStatus.NEW <= status <= TaskStatus.CANCEL
        return cls._texts[status]

    @classmethod
    def get_icon(cls, status):
        assert TaskStatus.NEW <= status <= TaskStatus.CANCEL
        return cls._glyphicons[status]


class Visibility(object):
    """
    Resource visibility to public/self/group/shared persons.
    """
    PRIVATE = 0         # visible to self
    # SHARED = 40       # visible to shared person only
    # PROTECTED = 70    # visible to team/group
    PUBLIC = 100       # visible to all
    _texts = {
        PUBLIC: pgettext_lazy('visibility', 'Public'),
        PRIVATE: pgettext_lazy('visibility', 'Private'),
        # PROTECTED: _('protected'),
        # SHARED: _('shared'),
    }
    _icons = {
        PUBLIC: 'fa fa-eye',
        PRIVATE: 'fa fa-eye-slash',
        # PROTECTED: 'fa fa-low-vision',
        # SHARED: 'fa fa-low-vision',
    }
    Choices = _texts.items()
    _items = {}

    @classmethod
    def get_items(cls):
        if not cls._items:
            for k, v in cls._texts.items():
                cls._items[k] = {'code': k, 'text': v, 'icon': cls.get_icon(k)}
        return cls._items

    @classmethod
    def get_text(cls, code):
        assert 0 <= code <= 100
        return cls._texts[code]

    @classmethod
    def get_icon(cls, code):
        assert 0 <= code <= 100
        return cls._icons[code]