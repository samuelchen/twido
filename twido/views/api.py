#!/usr/bin/env python
# coding: utf-8

"""
RESTful API view
"""

from django.contrib.auth import login
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from django.views import View
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseBadRequest,
    Http404,
    HttpResponseNotAllowed
)
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.views import login as login_func_view

from .base import BaseViewMixin
from ..models import UserProfileCreationForm
from ..models import SocialPlatform

import logging
log = logging.getLogger(__name__)


@method_decorator(require_http_methods(['POST', 'GET']), name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
# @method_decorator(never_cache, name='dispatch')
@method_decorator(sensitive_post_parameters(), name='dispatch')
class APIView(View, BaseViewMixin):

    def get(self, request):
        pass