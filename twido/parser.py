#!/usr/bin/env python
# coding: utf-8

"""
Parse given TIMEX3 XML and text to give out dates, simple text, tags and etc.
"""
import re

import dateparser
from pygments.lexers.html import XmlLexer
from pygments.formatters.html import HtmlFormatter
from pygments import highlight
from pyutils.langutil import MutableEnum

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import logging
log = logging.getLogger(__name__)


class Timex3Parser(object):

    _formatter = HtmlFormatter(encoding='utf-8', nowrap=False, style='emacs', linenos=False)
    _lexer = XmlLexer()
    _css = _formatter.get_style_defs()

    _re_hash = re.compile(r'(?:\A|\s)(?P<hash>#(?:\w|\.|_)+)(?:\s|\Z)', re.IGNORECASE + re.MULTILINE)

    def __init__(self):
        pass

    @classmethod
    def parse_task(cls, task, include_dates=True, include_title=True, include_labels=True, include_code=False):
        assert task and task.content

        if include_code: task.code = cls.highlight(task.content)
        if include_dates: task.dates = cls.parse_dates(task.content)
        if include_labels: task.labels = ','.join(cls.parse_hash_tags(task.text))
        if include_title: task.title = cls.parse_text(task.title)

        return task

    @classmethod
    def parse_text(cls, text):
        simple_text = text
        return simple_text

    @classmethod
    def parse_hash_tags(cls, text):
        """
        extract hash tags ("#" leading words) from given text
        :param text:
        :return:
        """
        tags = []

        for m in cls._re_hash.findall(text):
            tags.append(m[1:])      # ignore leading "#"

        return tags

    @staticmethod
    def parse_dates(timex3_xml):
        """
        extract all mentioned dates.
        :param timex3_xml:
        :return:
        """
        dates = []

        xml = ET.fromstring(timex3_xml)
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
            dates.append(dt)

        return dates

    @classmethod
    def highlight(cls, src):
        code = highlight(src, cls._lexer, cls._formatter)
        return code
    
    @classmethod
    def get_highlight_css(cls):
        return cls._css



def test_re():
    re_hashtag = re.compile(r'(?:\A|\s)(?P<hash>#(?:\w|\.|_)+)(?:\s|\Z)', re.IGNORECASE + re.MULTILINE)
    m = re_hashtag.findall('''#Looking for something #todo while in #LasVegas
    #partybus #trucklimo #limo #SUV #reserve one and have a
    #goodtime https://t.co/qlBi4BAcXF''')
    print(m)
    # print(m.groupdict()['hash'] if m else None)
    # print(m.group(0))
    # print(m.group(1))

    m = re_hashtag.findall('''#toDO RT HacksterPro... while in #LasVegas
    #partybus #trucklimo #limo #SUV #reserve one and have a
    #goodtime https://t.co/qlBi4BAcXF''')
    print(m)
    # print(m.groups() if m else None)

    m = re_hashtag.findall('''HacksterPro... while in #LasVegas
    #partybus #trucklimo #limo #SUV #reserve one and have a
    #goodtime https://t.co/qlBi4BAcXF blabla#WISH''')
    print(m)
    # print(m.groups() if m else None)

    m = re_hashtag.findall('''HacksterPro... while in #LasVegas
    #partybus #trucklimo #limo#SUV #reserve #WISHM.E one and have a
    #goodtime https://t.co/qlBi4BAcXF blabla''')
    print(m)
    # print(m.groups() if m else None)

# test_re()
# exit(0)
