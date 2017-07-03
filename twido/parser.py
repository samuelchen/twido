#!/usr/bin/env python
# coding: utf-8

"""
Parse given TIMEX3 XML and text to give out dates, simple text, tags and etc.
"""
import re
import parsedatetime
from datetime import datetime
from pygments.lexers.html import XmlLexer
from pygments.formatters.html import HtmlFormatter
from pygments import highlight

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import logging
log = logging.getLogger(__name__)


class Timex3Parser(object):

    _formatter = HtmlFormatter(encoding='utf-8', nowrap=False, style='emacs', linenos=False,
                               prestyles='font-size: 12px;')
    _lexer = XmlLexer()
    _css = _formatter.get_style_defs()

    _re_hash = re.compile(r'(?:\A|\s)(?P<hash>#(?:\w|\.|_)+)(?:\s|\Z)', re.IGNORECASE + re.MULTILINE)

    def __init__(self):
        pass

    @classmethod
    def parse_task(cls, task, include_dates=True, include_title=True, include_labels=True, include_code=False):

        if include_code: task.code = cls.highlight(task.content) if task.content else ''
        if include_dates: task.dates = cls.parse_dates(task.content) if task.content else []
        if include_labels: task.labels = ','.join(cls.parse_hash_tags(task.text))
        if include_title: task.title = cls.parse_text(task.title) or task.title

        return task

    @classmethod
    def parse_text(cls, text):
        simple_text = None
        return simple_text

    @classmethod
    def parse_hash_tags(cls, text):
        """
        extract hash tags ("#" leading words) from given text
        :param text:
        :return:
        """
        tags = []

        if text:
            for m in cls._re_hash.findall(text):
                tags.append(m[1:].lower())      # ignore leading "#"

        return tags

    @staticmethod
    def parse_dates(timex3_xml):
        """
        extract all mentioned dates.
        :param timex3_xml:
        :return:
        """
        dates = []
        cal = parsedatetime.Calendar()

        xml = ET.fromstring(timex3_xml)

        # base time
        node = xml.findtext("./DATE")
        base_time = datetime.strptime(node, '%a %b %d %H:%M:%S %z %Y')

        '''
        Fail dates:

            DURATION PT24H 24 hours
            DURATION P1D day
            SET P1D each day
            DURATION P1D day
            SET P1D Daily
            DURATION PT1M a Minute
            DURATION P1D day
            DURATION P1W Week
            DURATION P1W Week
            DURATION P1D day
            DURATION P1D day
            DURATION P1D Day
            SET P1D Daily
            DURATION P1D Day
            SET P1D Daily
            SET P1W Weekly
            SET P1W Weekly
            DURATION P22Y 22-year-old
            SET P1D daily
            DURATION P1W week
            SET TMO every morning
            DURATION P1W week
            SET TMO every morning
            DURATION P1W week
            SET TMO every morning
            DURATION P1D a day
            TIME T19:00 7pm
            DURATION PXY years
            SET P1D Daily
            SET P1D daily
            DURATION P1D One day
            DURATION P1D day
            DURATION P1D a day
            DURATION P1W a week
            DURATION P1M a month
            DURATION P1M a month
            DURATION PXY years
            DURATION P1D DAY
            TIME T19:00 7pm
            TIME TMO morning
            DURATION P21D Less than 21 days
            DURATION PT19S the last 19 seconds
            SET P1D Daily
            DURATION P1D day
            DURATION PXY years
            DURATION P1D Day
            SET P1D Daily
            DURATION P1D Day
            SET P1D Daily
            DURATION PXD days
            DURATION PT3M 3 mins
            DURATION P1W a week
            SET P1D daily
            SET P1D daily
            TIME TMO Morning
            DURATION P1W week
            DURATION PT40S more than 40 seconds
            SET P1D daily
            DURATION P1W Week
            SET P1D daily
            SET P1D daily
            DURATION P1W Week
            DURATION P9W 9 weeks
            DURATION P9W 9 weeks
            DURATION P1D one day
            DURATION P1D day
            DURATION P1D Day
            SET P1D Daily
            DURATION P1D day
            DURATION PXD few days
            SET P1D every day
            SET P1D every day
            SET P1W Weekly
            TIME TMO the next morning
            TIME TEV evening
            DURATION P1D day
            TIME TMO morning
        '''

        for node in xml.findall("./TEXT/TIMEX3"):
            dt = {}
            dt['text'] = node.text
            for k, v in node.items():
                dt[k] = v
            tp = dt['type']
            if dt['text']:
                if tp == 'DATE':
                    try:
                        # TODO: need to be parsed depends on date (when crawling)
                        value = dt['value']
                        # if value == 'PRESENT_REF':
                        #     v = dateparser.parse(dt['date'])
                        # elif value == 'PAST_REF':
                        #     v = None
                        #     pass
                        # elif value == 'FUTURE_REF':
                        #     v = None
                        #     pass
                        # elif value == 'XXXX':
                        #     v = dateparser.parse(dt['text'])
                        if value.startswith('XXXX-'):
                            # token = value.split('-')[1]
                            v = None
                            pass
                        else:
                            v = datetime(*cal.parse(dt['text'], sourceTime=base_time)[0][:6])
                        dt['v'] = v
                    except Exception as err:
                        log.warn(err)
                        dt['v'] = None
                elif tp == 'TIME':
                    dt['v'] = datetime(*cal.parse(dt['text'], sourceTime=base_time)[0][:6])
                elif tp == 'DURATION':
                    pass
                elif tp == 'SET':
                    pass
                else:
                    pass

                if 'v' in dt and dt['v']:
                    dates.append(dt)
                else:
                    log.warn('Fail/ignored date: %s %s %s' % (dt['type'], dt['value'], dt['text']))

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
