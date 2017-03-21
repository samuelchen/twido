#!/usr/bin/env python
# coding: utf-8

from django.core.management.base import BaseCommand
from services.spider import StorageType, TwitterSpider
from ...utils import load_config


class Command(BaseCommand):
    def add_arguments(self, parser):

        sb = []
        sb1 = []
        sum = 0
        for k, v in StorageType:
            sb.append('%s=%s' % (v, k))
            sb1.append(k)
            sum += v
        storage_help = 'Storage types. %s. Supports combination such as %d=%s (means save to all of %s).' % (', '.join(sb), sum, '+'.join(sb1), sb1)

        parser.add_argument(
            '--storage-types', '-t',
            action='store_true',
            dest='storage_types',
            default=1,
            help=storage_help,
        )

        parser.add_argument(
            '--config-file', '-f',
            action='store',
            type=str,
            dest='config_file',
            default='config.ini',
            help='Specify a config file. Default is config.ini',
        )

    def handle(self, *args, **options):
        config_file = options['config_file']
        cfgs = load_config(config_file=config_file)
        spider = TwitterSpider(consumer_key=cfgs.twitter.consumer_key,
                               consumer_secret=cfgs.twitter.consumer_secret,
                               access_token=cfgs.twitter.access_token,
                               access_token_secret=cfgs.twitter.access_token_secret,
                               storage=StorageType.FILE + StorageType.DB,
                               proxy=cfgs.common.proxy)
        spider.fetch()
