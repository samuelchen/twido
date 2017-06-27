#!/usr/bin/env python
# coding: utf-8

"""
Utilities
"""

import configparser
from pyutils.langutil import MutableEnum

import logging
log = logging.getLogger(__name__)


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


import dateparser
from pygments.lexers.html import XmlLexer
from pygments.formatters.html import HtmlFormatter
from pygments import highlight
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def html_highlight(tasks):

    formatter = HtmlFormatter(encoding='utf-8', nowrap=False, style='emacs', linenos=False)
    lexer = XmlLexer()

    for task in tasks:

        task.dates = []
        task.code = None

        if not task.content:
            continue

        task.code = highlight(task.content, lexer, formatter)
        # print(task.title)
        xml = ET.fromstring(task.content)
        for node in xml.findall("./TEXT/TIMEX3"):
            dt = MutableEnum()
            dt.text = node.text
            # print(node.text)
            for k, v in node.items():
                # print('  ', k, v)
                dt[k] = v
            if dt.type == 'DATE' and dt.text:
                try:
                    dt.v = dateparser.parse(dt.text)
                    # dt.v = parse_datetime(dt.text)
                except Exception as err:
                    log.warn(err)
                    dt.v = None
            task.dates.append(dt)

    return tasks, formatter.get_style_defs()