#!/usr/bin/env python
# coding: utf-8

from pyutils.timing_wheel import TimingWheel, IRemind
from twido.models import Task
from django.utils import timezone


class Reminder(object):

    def __init__(self):
        self._timer = TimingWheel()

    def start(self):
        start = timezone.now()
        end = start + timezone.timedelta(days=1)

        for task in Task.objects.filter(due__gte=start, due__lte=end):
            self._timer.push(task.due, task)
        self._timer.start()
        print(self._timer._wheel)

    def stop(self):
        self._timer.stop()
