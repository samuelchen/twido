#!/usr/bin/env python
# coding: utf-8

from django.core.management.base import BaseCommand
from twido.models import TodoList, WishList
from services.storage import StorageType
from services.parser import TwitterParser
from ...utils import load_config


class Command(BaseCommand):
    def get_storage_help(self):
        sb = []
        sb1 = []
        sum = 0
        for k, v in StorageType:
            sb.append('%s=%s' % (v, k))
            sb1.append(k)
            sum += v
        return 'Storage types. %s. Supports combination such as %d=%s (means save to all of %s).' % (', '.join(sb), sum, '+'.join(sb1), sb1)

    def add_arguments(self, parser):

        parser.add_argument(
            '--storage-types', '-t',
            action='store',
            dest='storage_types',
            type=int,
            default=1,
            help=self.get_storage_help(),
        )

        parser.add_argument(
            '--config-file', '-f',
            action='store',
            type=str,
            dest='config_file',
            default='config.ini',
            help='Specify a config file. Default is config.ini',
        )

        pass

    def handle(self, *args, **options):
        config_file = options['config_file']
        storage = int(options['storage_types'])
        cfgs = load_config(config_file=config_file)
        WishList.init_data()