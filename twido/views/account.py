#!/usr/bin/env python
# coding: utf-8
from django.contrib.auth import login
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.views import login as login_func_view

from ..forms import UserProfileCreationForm
import logging
from .base import BaseViewMixin

log = logging.getLogger(__name__)


class I18N_MSGS(object):
    reg_success = _('Registration succeed.')
    redirect_to_profile = _('Redirect to profile updating page ... <br>'
                            'If redirection did not start, please <a href="%s">click me to profile</a>.')


@method_decorator(require_http_methods(['POST', 'GET']), name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(never_cache, name='dispatch')
@method_decorator(sensitive_post_parameters(), name='dispatch')
class RegisterView(TemplateView, BaseViewMixin):
    def get_context_data(self, **kwargs):
        context = super(RegisterView, self).get_context_data(**kwargs)
        success = False
        profile = None
        request = self.request

        if request.method == "POST":
            form = UserProfileCreationForm(data=self.request.POST)
            if form.is_valid():
                profile = form.save()
                success = True
            else:
                if 'username' in form.errors:
                    del form.errors['username']
        else:
            form = UserProfileCreationForm()

        context['form'] = form
        context['success'] = success

        if success and profile and profile.user and profile.user.is_active:
            login(request, profile.user)
            self.success(I18N_MSGS.reg_success)
            self.success(I18N_MSGS.redirect_to_profile % reverse('profile'))

        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


@method_decorator(require_http_methods(['POST', 'GET']), name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(never_cache, name='dispatch')
@method_decorator(sensitive_post_parameters(), name='dispatch')
class LoginView(TemplateView, BaseViewMixin):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.login(request, template_name=self.template_name, extra_context=context, **kwargs)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.login(request, template_name=self.template_name, extra_context=context, **kwargs)

    def login(self, request, template_name='registration/login.html',
              # redirect_field_name=REDIRECT_FIELD_NAME,
              # authentication_form=AuthenticationForm,
              extra_context=None, redirect_authenticated_user=False):
        print(extra_context)
        return login_func_view(request, template_name=template_name,
                               # redirect_field_name=redirect_field_name,
                               # authentication_form=authentication_form,
                               extra_context=extra_context,
                               redirect_authenticated_user=redirect_authenticated_user)