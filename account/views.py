#!/usr/bin/env python
# coding: utf-8

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import User


def userDemo(request):
    desc = User.objects.all()[0]
    return HttpResponse(desc.email)