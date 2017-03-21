#!/usr/bin/env python
# coding: utf-8

import logging
import logging.config

with open('logging.ini', 'rt', encoding='utf-8') as f:
    logging.config.fileConfig(f)
log = logging.getLogger(__name__)

log.debug('hello')