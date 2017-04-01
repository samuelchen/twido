#!/usr/bin/env python
# coding: utf-8

"""
views
"""

from django.conf import settings
from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.urls import reverse

import logging
log = logging.getLogger(__name__)


# to render full template path
def t(template):
    return 'twido/' + template


# test view for some test purpose
if __debug__ and settings.DEBUG:
    def test(request):
        return render(request, t('test.html'))


@require_http_methods(['GET', ])
def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = 'authoried'
    elif request.user.is_staff:
        context['user'] = 'staff'
    else:
        context['user'] = 'forbiden'
    # context = {
    #     # "setting_keys": models.SETTING_NAMES,
    # }
    return render(request, t('index.html'), context=context)
