#!/usr/bin/env python
# coding: utf-8

from django.core.management.base import BaseCommand
from services.reminder import Reminder
from ...utils import load_config


class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument(
            '--max', '-m',
            action='store',
            dest='max',
            type=int,
            default=0,
            help='Max count to fetch.',
        )

        parser.add_argument(
            '--test', '-e',
            action='store_true',
            dest='test',
            default=False,
            help='If test specified, will only fetch tester users.',
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
        reminder = Reminder()
        reminder.start()

