#!/usr/bin/env python
# coding: utf-8

"""
Middle wares
"""

from django.utils.deprecation import MiddlewareMixin
from twido.models import UserProfile


class RequestProfileMiddleWare(MiddlewareMixin):

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        profile = UserProfile.objects.get(user=request.user)
        request.profile = profile
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response