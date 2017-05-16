#!/usr/bin/env python
# coding: utf-8

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from ..forms import UserProfileCreationForm
from ..models import UserProfile, Config
import logging
log = logging.getLogger(__name__)


@sensitive_post_parameters('password', 'password2')
@csrf_protect
@never_cache
def register(request):
    success = False
    profile = None

    if request.method == "POST":
        form = UserProfileCreationForm(data=request.POST)
        if form.is_valid():
            profile = form.save()
            success = True
        else:
            if 'username' in form.errors:
                del form.errors['username']
    else:
        form = UserProfileCreationForm()

    context = {
        'form': form,
        'success': success,
    }

    if success and profile and profile.user and profile.user.is_active:
        login(request, profile.user)
        messages.success(request, _('Registration succeed.'), '', fail_silently=True)
        messages.success(request, _('Redirect to profile updating page ...'), '', fail_silently=True)
        messages.success(request,
                         _('If redirection did not start, please <a href="%s">click me to profile</a>.') % reverse(
                             'profile'), '', fail_silently=True)

    if 'theme' not in context:
        try:
            profile = request.user.profile
        except:
            profile = UserProfile.get_sys_profile()
        opt = Config.get_user_conf(profile, 'theme')
        context['theme'] = opt.value if opt else 'simplex'

    return render(request, 'registration/register.html', context)


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
