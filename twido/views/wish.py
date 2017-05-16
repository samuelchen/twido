#!/usr/bin/env python
# coding: utf-8

from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView, DetailView, CreateView, DeleteView
from django.utils.translation import ugettext as _
from ..models import Todo,  TodoList, TaskStatus, WishList
from .base import BaseViewMixin
from .common import paginate

import logging
log = logging.getLogger(__name__)


class WishListView(TemplateView, BaseViewMixin):

    def get_context_data(self, **kwargs):
        context = super(WishListView, self).get_context_data(**kwargs)
        profile = self.request.user.profile

        if 'pk' in context:
            pk = context['pk']
            thelist = get_object_or_404(TodoList, id=pk)
        else:
            thelist = TodoList.get_default(profile)

        context['thelist'] = thelist
        if 'lists' not in context:
            context['lists'] = WishList.objects.filter(profile=profile).all()




