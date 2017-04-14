#!/usr/bin/env python
# coding: utf-8

"""
Utilities
"""

import configparser
from pyutils.langutil import MutableEnum


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