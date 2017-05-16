#!/usr/bin/env python
# coding: utf-8

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .base import BaseViewMixin
from ..models import SocialAccount, TodoList, WishList


@method_decorator(login_required, 'dispatch')
class HomeView(TemplateView, BaseViewMixin):
    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        profile = self.request.user.profile
        accs = SocialAccount.objects.filter(profile=profile).values_list('platform')

        context['todolists'] = TodoList.objects.filter(profile=profile).all()
        context['wishlists'] = WishList.objects.filter(profile=profile).all()
        # context['wishlists'] = Wish.objects.filter(Q(profile=profile) | Q(social_account__in=accs)).all()
        return context
