#!/usr/bin/env python
# coding: utf-8

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect
from django.utils import translation
from django.views.decorators.http import require_http_methods
from ..models import UserProfile, Config
import logging
log = logging.getLogger(__name__)


@require_http_methods(['GET', ])
def test(request, pk=None):
    if not settings.DEBUG:
        return redirect('/')

    log.debug('%s %s %s' % (request, pk, request.POST))
    context = {}

    if request.method == "POST":
        pass
    else:
        pass

    signin = request.GET.get('signin', None)
    if signin:
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(username=signin)
            login(request, user)
        except UserModel.DoesNotExist:
            pass
        return redirect('home')

    if 'theme' not in context:
        try:
            profile = request.user.profile
        except:
            profile = UserProfile.get_sys_profile()
        opt = Config.get_user_conf(profile, 'theme')
        context['theme'] = opt.value if opt else 'simplex'

    if pk == '1':
        messages.debug(request, 'This is debug message', fail_silently=True)
        messages.info(request, 'This is info message', fail_silently=True)
        messages.warning(request, 'This is warning message', fail_silently=True)
        messages.error(request, 'This is error message', fail_silently=True)
        messages.success(request, 'This is success message', fail_silently=True)
        messages.add_message(request, messages.WARNING, 'This is a WARN message added.', 'danger', fail_silently=True)

    if not profile.is_faked and 'LANGUAGE_CODE' not in context:
        opt = Config.get_user_conf(profile, 'lang')
        context['LANGUAGE_CODE'] = opt.value if opt else 'en'
        translation.activate(context['LANGUAGE_CODE'])

    return render(request, 'test/test%s.html' % (pk if pk else ''), context=context)


def paginate(objects, cur_page=1, entries_per_page=15):
    paginator = Paginator(objects, entries_per_page)

    page = None
    try:
        page = paginator.page(cur_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page = paginator.page(paginator.num_pages)

    return page
